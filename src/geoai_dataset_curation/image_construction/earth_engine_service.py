"Validated orchestration service for Earth Engine provider operations"

from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineProvider,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
)
from geoai_dataset_curation.image_construction.earth_engine_provider_validation import (
    validate_earth_engine_composite_request,
    validate_earth_engine_export_request,
    validate_earth_engine_scene_query,
)


class EarthEngineService:
    "Validate domain requests before delegating them to a provider"
    def __init__(self, provider: EarthEngineProvider) -> None:
        self._provider = provider

    def search_sentinel2_scenes(
        self,
        query: EarthEngineSceneQuery,
    ) -> tuple[EarthEngineSceneReference, ...]:
        "Validate and execute one Sentinel-2 scene query"
        errors = validate_earth_engine_scene_query(query)

        if errors:
            raise ValueError(
                "Invalid Earth Engine scene query: "
                + "; ".join(errors)
            )
        return self._provider.search_sentinel2_scenes(query)

    def build_composite(
        self,
        request: EarthEngineCompositeRequest,
    ) -> EarthEngineImageReference:
        "Validate and execute one composite request"
        errors = validate_earth_engine_composite_request(request)

        if errors:
            raise ValueError(
                "Invalid Earth Engine composite request: "
                + "; ".join(errors)
            )
        return self._provider.build_composite(request)

    def start_export(
        self,
        request: EarthEngineExportRequest,
    ) -> EarthEngineExportTaskReference:
        "Validate and start one exact-grid export"
        errors = validate_earth_engine_export_request(request)

        if errors:
            raise ValueError(
                "Invalid Earth Engine export request: "
                + "; ".join(errors)
            )
        return self._provider.start_export(request)

    def get_export_status(
        self,
        task: EarthEngineExportTaskReference,
    ) -> EarthEngineExportTaskStatus:
        "Return the normalized status of one export task"
        if not task.task_id.strip():
            raise ValueError(
                "Invalid Earth Engine export task: "
                "task_id must not be empty."
            )
        return self._provider.get_export_status(task)