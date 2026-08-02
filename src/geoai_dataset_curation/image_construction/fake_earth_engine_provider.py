"Controllable fake implementation of the Earth Engine provider boundary"

from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineTaskState,
)


class FakeEarthEngineProvider:
    "Fake provider for deterministic image-construction tests"
    def __init__(
        self,
        *,
        scene_results: tuple[EarthEngineSceneReference, ...] = (),
        composite_image_id: str = "fake-composite",
        export_task_id: str = "fake-export-task",
        export_status: EarthEngineExportTaskStatus | None = None,
    ) -> None:
        self.scene_results = scene_results
        self.composite_image_id = composite_image_id
        self.export_task_id = export_task_id
        self.export_status = export_status or EarthEngineExportTaskStatus(
            task_id=export_task_id,
            state=EarthEngineTaskState.COMPLETED,
        )
        self.scene_queries: list[EarthEngineSceneQuery] = []
        self.composite_requests: list[EarthEngineCompositeRequest] = []
        self.export_requests: list[EarthEngineExportRequest] = []
        self.status_requests: list[EarthEngineExportTaskReference] = []

    def search_sentinel2_scenes(
        self,
        query: EarthEngineSceneQuery,
    ) -> tuple[EarthEngineSceneReference, ...]:
        "Record one query and return configured scene results"
        self.scene_queries.append(query)
        return self.scene_results

    def build_composite(
        self,
        request: EarthEngineCompositeRequest,
    ) -> EarthEngineImageReference:
        "Record one request and return a configured image reference"
        self.composite_requests.append(request)
        return EarthEngineImageReference(
            image_id=self.composite_image_id,
        )

    def start_export(
        self,
        request: EarthEngineExportRequest,
    ) -> EarthEngineExportTaskReference:
        "Record one export request and return a configured task reference"
        self.export_requests.append(request)
        return EarthEngineExportTaskReference(
            task_id=self.export_task_id,
        )

    def get_export_status(
        self,
        task: EarthEngineExportTaskReference,
    ) -> EarthEngineExportTaskStatus:
        "Record one status request and return a configured task status"
        self.status_requests.append(task)
        return self.export_status