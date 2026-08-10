"Provider boundary for Earth Engine image construction"
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable
from geoai_dataset_curation.image_construction.contracts import (
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from enum import StrEnum


@dataclass(frozen=True)
class EarthEngineSceneQuery:
    "Provider-neutral request for Sentinel-2 scene discovery"
    collection_id: str
    start_date: str
    end_date: str
    aoi_geojson: dict[str, object]
    maximum_cloud_cover: float


@dataclass(frozen=True)
class EarthEngineSceneReference:
    "Reference to one Earth Engine scene selected by the provider"
    scene_id: str
    acquisition_date: str
    cloud_cover: float


class EarthEngineAggregationMethod(StrEnum):
    "Supported temporal aggregation methods"
    MEDIAN = "median"


@dataclass(frozen=True)
class EarthEngineCompositeRequest:
    "Request for constructing one Sentinel-2 image composite"
    scene_ids: tuple[str, ...]
    bands: tuple[str, ...]
    cloud_mask: Sentinel2CloudMaskSpec
    aggregation_method: EarthEngineAggregationMethod


@dataclass(frozen=True)
class EarthEngineImageReference:
    "Opaque reference to one provider-managed Earth Engine image"
    image_id: str


@dataclass(frozen=True)
class EarthEngineExportRequest:
    "Request for exporting one Earth Engine image on an exact grid"
    image: EarthEngineImageReference
    output_name: str
    grid: RasterGridSpec


class EarthEngineTaskState(StrEnum):
    "Normalized lifecycle states for one Earth Engine export task"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class EarthEngineExportTaskReference:
    "Reference to one Earth Engine export task"
    task_id: str


@dataclass(frozen=True)
class EarthEngineExportTaskStatus:
    "Normalized status returned for one Earth Engine export task"
    task_id: str
    state: EarthEngineTaskState
    error_message: str | None = None

    @property
    def is_terminal(self) -> bool:
        "Return whether the export task has reached a terminal state"
        return self.state in {
            EarthEngineTaskState.COMPLETED,
            EarthEngineTaskState.FAILED,
            EarthEngineTaskState.CANCELLED,
        }

    @property
    def succeeded(self) -> bool:
        "Return whether the export task completed successfully"
        return self.state is EarthEngineTaskState.COMPLETED


@runtime_checkable
class EarthEngineProvider(Protocol):
    "Boundary implemented by Earth Engine service adapters"
    def search_sentinel2_scenes(
        self,
        query: EarthEngineSceneQuery,
    ) -> tuple[EarthEngineSceneReference, ...]:
        "Return Sentinel-2 scenes matching one provider-neutral query"
        ...

    def build_composite(
        self,
        request: EarthEngineCompositeRequest,
    ) -> EarthEngineImageReference:
        "Build a composite and return an opaque image reference"
        ...

    def start_export(
        self,
        request: EarthEngineExportRequest,
    ) -> EarthEngineExportTaskReference:
        "Start an exact-grid image export"
        ...

    def get_export_status(
        self,
        task: EarthEngineExportTaskReference,
    ) -> EarthEngineExportTaskStatus:
        "Return the normalized status of one export task"
        ...