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
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
)


CLOUD_COVER_PROPERTY = "CLOUDY_PIXEL_PERCENTAGE"
SYSTEM_INDEX_PROPERTY = "system:index"
ACQUISITION_TIME_PROPERTY = "system:time_start"


class EarthEngineSdkProvider:
    "Execute Earth Engine provider operations through the Python SDK"
    def __init__(
        self,
        *,
        sdk: Any = ee,
    ) -> None:
        self._sdk = sdk

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