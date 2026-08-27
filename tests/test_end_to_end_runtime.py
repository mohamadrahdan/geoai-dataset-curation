from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineTaskState,
)
from geoai_dataset_curation.image_construction.earth_engine_service import (
    EarthEngineService,
)
from geoai_dataset_curation.image_construction.end_to_end_runtime import (
    execute_earth_engine_image_flow,
)
from geoai_dataset_curation.image_construction.fake_earth_engine_provider import (
    FakeEarthEngineProvider,
)
import pytest

def _grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=16,
        height=8,
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


def _query() -> EarthEngineSceneQuery:
    return EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-05-01",
        end_date="2024-05-31",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [51.0, 30.0],
                    [51.1, 30.0],
                    [51.1, 30.1],
                    [51.0, 30.1],
                    [51.0, 30.0],
                ]
            ],
        },
        maximum_cloud_cover=20.0,
    )


def _composite_request(
    scenes: tuple[EarthEngineSceneReference, ...],
) -> EarthEngineCompositeRequest:
    return EarthEngineCompositeRequest(
        scene_ids=tuple(
            scene.scene_id
            for scene in scenes
        ),
        bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=(
            EarthEngineAggregationMethod.MEDIAN
        ),
    )


def _export_request(
    image: EarthEngineImageReference,
) -> EarthEngineExportRequest:
    return EarthEngineExportRequest(
        image=image,
        output_name="padena_sentinel2_image",
        grid=_grid(),
        destination=(EarthEngineExportDestination.DRIVE),
        destination_folder="padena-images",
    )


def test_execute_earth_engine_image_flow_integrates_provider_operations() -> None:
    scene = EarthEngineSceneReference(
        scene_id="scene-1",
        acquisition_date="2024-05-18",
        cloud_cover=8.5,
    )

    provider = FakeEarthEngineProvider(
        scene_results=(
            scene,
        ),
        composite_image_id="composite-1",
        export_task_id="task-1",
        export_status=EarthEngineExportTaskStatus(
            task_id="task-1",
            state=EarthEngineTaskState.COMPLETED,
        ),
    )

    service = EarthEngineService(provider)

    result = execute_earth_engine_image_flow(
        service=service,
        scene_query=_query(),
        composite_request_factory=_composite_request,
        export_request_factory=_export_request,
        poll_interval_seconds=0.0,
        sleep_fn=lambda _: None,
    )

    assert result.scenes == (scene,)
    assert (result.composite.image_id == "composite-1")
    assert (result.export_task.task_id == "task-1")
    assert result.final_status.succeeded
    assert provider.scene_queries == [_query()]
    assert len(provider.composite_requests) == 1
    assert (provider.composite_requests[0].scene_ids == ("scene-1",))
    assert len(provider.export_requests) == 1
    assert (provider.export_requests[0].image.image_id == "composite-1")
    assert provider.status_requests == [result.export_task]


def test_execute_earth_engine_image_flow_stops_when_no_scenes_are_returned() -> None:
    provider = FakeEarthEngineProvider()
    service = EarthEngineService(provider)

    with pytest.raises(
        ValueError,
        match="No Sentinel-2 scenes",
    ):
        execute_earth_engine_image_flow(
            service=service,
            scene_query=_query(),
            composite_request_factory=_composite_request,
            export_request_factory=_export_request,
            sleep_fn=lambda _: None,
        )

    assert len(provider.scene_queries) == 1
    assert provider.composite_requests == []
    assert provider.export_requests == []
    assert provider.status_requests == []


def test_execute_earth_engine_image_flow_rejects_failed_export() -> None:
    provider = FakeEarthEngineProvider(
        scene_results=(
            EarthEngineSceneReference(
                scene_id="scene-1",
                acquisition_date="2024-05-18",
                cloud_cover=8.5,
            ),
        ),
        export_task_id="task-1",
        export_status=EarthEngineExportTaskStatus(
            task_id="task-1",
            state=EarthEngineTaskState.FAILED,
            error_message="export failed",
        ),
    )

    service = EarthEngineService(
        provider
    )

    with pytest.raises(
        RuntimeError,
        match="failed",
    ):
        execute_earth_engine_image_flow(
            service=service,
            scene_query=_query(),
            composite_request_factory=_composite_request,
            export_request_factory=_export_request,
            poll_interval_seconds=0.0,
            sleep_fn=lambda _: None,
        )