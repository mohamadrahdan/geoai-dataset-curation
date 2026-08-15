"Earth Engine provider backed by the real Python SDK"
from __future__ import annotations
from datetime import date, timedelta
from typing import Any
import ee
from requests.exceptions import RequestException
from geoai_dataset_curation.image_construction.earth_engine_errors import (
    EarthEngineConnectionError,
    EarthEngineRequestError,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineAggregationMethod,
    EarthEngineExportDestination,
    EarthEngineTaskState,
)
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)


CLOUD_COVER_PROPERTY = "CLOUDY_PIXEL_PERCENTAGE"
SYSTEM_INDEX_PROPERTY = "system:index"
ACQUISITION_TIME_PROPERTY = "system:time_start"


def _apply_sentinel2_cloud_mask(
    image: Any,
    spec: Sentinel2CloudMaskSpec,
) -> Any:
    "Apply one validated Sentinel-2 SCL cloud-mask policy"
    scl = image.select(spec.scl_band)
    clear_mask = scl.remap(
        list(spec.excluded_scl_classes),
        [0] * len(spec.excluded_scl_classes),
        1,
    )
    return image.updateMask(clear_mask)

def _build_drive_export_parameters(
    *,
    sdk: Any,
    image: Any,
    request: EarthEngineExportRequest,
) -> dict[str, Any]:
    "Translate one exact-grid export request to Earth Engine parameters"
    transform = request.grid.transform
    if transform is None:
        raise ValueError(
            "Earth Engine export requires an exact raster transform."
        )

    left = transform.c
    top = transform.f
    right = left + request.grid.width * transform.a
    bottom = top + request.grid.height * transform.e
    region = sdk.Geometry.Rectangle(
        [
            left,
            bottom,
            right,
            top,
        ],
        request.grid.crs,
        False,
    )
    return {
        "image": image,
        "description": request.output_name,
        "folder": request.destination_folder,
        "fileNamePrefix": request.output_name,
        "region": region,
        "crs": request.grid.crs,
        "crsTransform": list(
            transform.as_tuple
        ),
        "fileFormat": "GeoTIFF",
    }

def _normalize_export_task_state(
    raw_state: str,
) -> EarthEngineTaskState:
    """Normalize one Earth Engine SDK task state."""

    state_mapping = {
        "READY": EarthEngineTaskState.READY,
        "RUNNING": EarthEngineTaskState.RUNNING,
        "COMPLETED": EarthEngineTaskState.COMPLETED,
        "FAILED": EarthEngineTaskState.FAILED,
        "CANCELLED": EarthEngineTaskState.CANCELLED,
        "CANCEL_REQUESTED": EarthEngineTaskState.RUNNING,
    }

    try:
        return state_mapping[raw_state]
    except KeyError as exc:
        raise ValueError(
            "Unsupported Earth Engine task state: "
            f"{raw_state}"
        ) from exc

class EarthEngineSdkProvider:
    "Execute Earth Engine provider operations through the Python SDK"
    def __init__(
        self,
        *,
        sdk: Any = ee,
    ) -> None:
        self._sdk = sdk
        self._images: dict[str, Any] = {}
        self._tasks: dict[str, Any] = {}

    def search_sentinel2_scenes(
        self,
        query: EarthEngineSceneQuery,
    ) -> tuple[EarthEngineSceneReference, ...]:
        "Search Sentinel-2 scenes and return normalized references"
        try:
            aoi = self._sdk.Geometry(query.aoi_geojson)

            end_exclusive = (
                date.fromisoformat(query.end_date)
                + timedelta(days=1)
            ).isoformat()

            collection = (
                self._sdk.ImageCollection(query.collection_id)
                .filterDate(
                    query.start_date,
                    end_exclusive,
                )
                .filterBounds(aoi)
                .filter(
                    self._sdk.Filter.lte(
                        CLOUD_COVER_PROPERTY,
                        query.maximum_cloud_cover,
                    )
                )
                .sort(ACQUISITION_TIME_PROPERTY)
            )

            result = collection.getInfo()

        except RequestException as error:
            raise EarthEngineConnectionError(
                "Earth Engine scene search could not reach the service."
            ) from error
        except Exception as error:
            raise EarthEngineRequestError(
                "Earth Engine scene search failed."
            ) from error

        features = result.get("features", [])
        scene_references: list[EarthEngineSceneReference] = []

        for feature in features:
            properties = feature.get("properties", {})
            scene_id = feature.get("id") or properties.get(
                SYSTEM_INDEX_PROPERTY,
                "",
            )
            acquisition_time = properties.get(
                ACQUISITION_TIME_PROPERTY
            )
            cloud_cover = properties.get(
                CLOUD_COVER_PROPERTY
            )
            if (
                not scene_id
                or acquisition_time is None
                or cloud_cover is None
            ):
                raise EarthEngineRequestError(
                    "Earth Engine scene metadata is incomplete."
                )
            acquisition_date = (
                self._sdk.Date(acquisition_time)
                .format("YYYY-MM-dd")
                .getInfo()
            )
            scene_references.append(
                EarthEngineSceneReference(
                    scene_id=str(scene_id),
                    acquisition_date=str(acquisition_date),
                    cloud_cover=float(cloud_cover),
                )
            )
        return tuple(scene_references)


    def build_composite(
        self,
        request: EarthEngineCompositeRequest,
    ) -> EarthEngineImageReference:
        "Build a cloud-masked Sentinel-2 temporal composite"
        try:
            images = []
            for scene_id in request.scene_ids:
                image = self._sdk.Image(scene_id)
                masked_image = _apply_sentinel2_cloud_mask(
                    image,
                    request.cloud_mask,
                )
                selected_image = masked_image.select(
                    list(request.bands)
                )

                images.append(selected_image)
            collection = self._sdk.ImageCollection.fromImages(
                images
            )

            if (
                request.aggregation_method
                == EarthEngineAggregationMethod.MEDIAN
            ):
                composite = collection.median()
            else:
                raise ValueError(
                    "Unsupported Earth Engine aggregation method: "
                    f"{request.aggregation_method}"
                )
            image_id = (
                "sentinel2-composite:"
                f"{request.aggregation_method.value}:"
                f"{len(request.scene_ids)}-scenes"
            )
            self._images[image_id] = composite
            return EarthEngineImageReference(
                image_id=image_id
            )

        except RequestException as exc:
            raise EarthEngineConnectionError(
                "Earth Engine composite construction failed "
                "because of a connection error."
            ) from exc
        except EarthEngineConnectionError:
            raise
        except Exception as exc:
            raise EarthEngineRequestError(
                "Earth Engine composite construction failed."
            ) from exc

    def start_export(
        self,
        request: EarthEngineExportRequest,
    ) -> EarthEngineExportTaskReference:
        "Start one exact-grid Earth Engine image export"
        try:
            image_id = request.image.image_id
            if image_id not in self._images:
                raise ValueError(
                    "Earth Engine image reference could not be resolved: "
                    f"{image_id}"
                )

            image = self._images[image_id]
            if (
                request.destination
                != EarthEngineExportDestination.DRIVE
            ):
                raise ValueError(
                    "Unsupported Earth Engine export destination: "
                    f"{request.destination}"
                )
            params = _build_drive_export_parameters(
                sdk=self._sdk,
                image=image,
                request=request,
            )
            task = self._sdk.batch.Export.image.toDrive(
                **params
            )
            task.start()
            task_id = task.id
            self._tasks[task_id] = task
            return EarthEngineExportTaskReference(
                task_id=task_id
)

        except RequestException as exc:
            raise EarthEngineConnectionError(
                "Earth Engine export task could not reach the service."
            ) from exc
        except EarthEngineConnectionError:
            raise
        except Exception as exc:
            raise EarthEngineRequestError(
                "Earth Engine export task could not be started."
            ) from exc

    def get_export_status(
        self,
        task: EarthEngineExportTaskReference,
    ) -> EarthEngineExportTaskStatus:
        "Return normalized status for one Earth Engine export task"
        try:
            if task.task_id not in self._tasks:
                raise ValueError(
                    "Earth Engine export task reference "
                    "could not be resolved: "
                    f"{task.task_id}"
                )
            sdk_task = self._tasks[
                task.task_id
            ]
            raw_status = sdk_task.status()
            raw_state = str(
                raw_status["state"]
            )
            state = _normalize_export_task_state(
                raw_state
            )
            error_message = raw_status.get(
                "error_message"
            )
            return EarthEngineExportTaskStatus(
                task_id=task.task_id,
                state=state,
                error_message=error_message,
            )
        except RequestException as exc:
            raise EarthEngineConnectionError(
                "Earth Engine export task status "
                "could not reach the service."
            ) from exc
        except EarthEngineConnectionError:
            raise
        except Exception as exc:
            raise EarthEngineRequestError(
                "Earth Engine export task status "
                "could not be retrieved."
            ) from exc