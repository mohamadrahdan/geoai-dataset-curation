from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineTaskState,
    RasterGridSpec,
    Sentinel2CloudMaskSpec,
)


def test_earth_engine_scene_query_stores_provider_neutral_inputs() -> None:
    query = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-06-01",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=20.0,
    )
    assert query.collection_id == "COPERNICUS/S2_SR_HARMONIZED"
    assert query.start_date == "2024-06-01"
    assert query.end_date == "2024-09-30"
    assert query.maximum_cloud_cover == 20.0


def test_earth_engine_scene_reference_stores_selected_scene_metadata() -> None:
    scene = EarthEngineSceneReference(
        scene_id="COPERNICUS/S2_SR_HARMONIZED/example",
        acquisition_date="2024-07-15",
        cloud_cover=8.5,
    )
    assert scene.scene_id.endswith("/example")
    assert scene.acquisition_date == "2024-07-15"
    assert scene.cloud_cover == 8.5


def test_earth_engine_composite_request_stores_processing_contract() -> None:
    cloud_mask = Sentinel2CloudMaskSpec()
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-2"),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=cloud_mask,
    )
    assert request.scene_ids == ("scene-1", "scene-2")
    assert request.bands == ("B2", "B3", "B4", "B8")
    assert request.cloud_mask == cloud_mask


def test_earth_engine_export_request_uses_exact_raster_grid() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        ),
    )
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:padena-sentinel2"
        ),
        output_name="padena_sentinel2_stack",
        grid=grid,
    )
    assert request.image.image_id == "composite:padena-sentinel2"
    assert request.output_name == "padena_sentinel2_stack"
    assert request.grid == grid


def test_export_task_status_reports_non_terminal_running_state() -> None:
    status = EarthEngineExportTaskStatus(
        task_id="task-001",
        state=EarthEngineTaskState.RUNNING,
    )
    assert status.is_terminal is False
    assert status.succeeded is False
    assert status.error_message is None


def test_export_task_status_reports_successful_terminal_state() -> None:
    status = EarthEngineExportTaskStatus(
        task_id="task-001",
        state=EarthEngineTaskState.COMPLETED,
    )
    assert status.is_terminal is True
    assert status.succeeded is True


def test_export_task_status_reports_failed_terminal_state() -> None:
    task = EarthEngineExportTaskReference(task_id="task-001")
    status = EarthEngineExportTaskStatus(
        task_id=task.task_id,
        state=EarthEngineTaskState.FAILED,
        error_message="Export quota exceeded.",
    )
    assert status.is_terminal is True
    assert status.succeeded is False
    assert status.error_message == "Export quota exceeded."