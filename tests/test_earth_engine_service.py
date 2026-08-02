import pytest
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineService,
    EarthEngineTaskState,
    FakeEarthEngineProvider,
    RasterGridSpec,
)


def make_exact_grid() -> RasterGridSpec:
    return RasterGridSpec(
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


def test_service_validates_and_delegates_scene_search() -> None:
    scenes = (
        EarthEngineSceneReference(
            scene_id="scene-1",
            acquisition_date="2024-07-10",
            cloud_cover=5.0,
        ),
    )
    provider = FakeEarthEngineProvider(scene_results=scenes)
    service = EarthEngineService(provider)
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

    result = service.search_sentinel2_scenes(query)
    assert result == scenes
    assert provider.scene_queries == [query]


def test_service_rejects_invalid_scene_query_before_delegation() -> None:
    provider = FakeEarthEngineProvider()
    service = EarthEngineService(provider)
    query = EarthEngineSceneQuery(
        collection_id=" ",
        start_date="invalid",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Point",
        },
        maximum_cloud_cover=120.0,
    )

    with pytest.raises(
        ValueError,
        match="Invalid Earth Engine scene query",
    ):
        service.search_sentinel2_scenes(query)

    assert provider.scene_queries == []


def test_service_validates_and_delegates_composite_request() -> None:
    provider = FakeEarthEngineProvider(
        composite_image_id="composite:padena"
    )
    service = EarthEngineService(provider)
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-2"),
        bands=("B2", "B3", "B4", "B8"),
    )

    result = service.build_composite(request)
    assert result == EarthEngineImageReference(
        image_id="composite:padena"
    )
    assert provider.composite_requests == [request]


def test_service_rejects_invalid_composite_before_delegation() -> None:
    provider = FakeEarthEngineProvider()
    service = EarthEngineService(provider)
    request = EarthEngineCompositeRequest(
        scene_ids=(),
        bands=(),
    )

    with pytest.raises(
        ValueError,
        match="Invalid Earth Engine composite request",
    ):
        service.build_composite(request)

    assert provider.composite_requests == []


def test_service_validates_and_delegates_export_request() -> None:
    provider = FakeEarthEngineProvider(
        export_task_id="task-123"
    )
    service = EarthEngineService(provider)
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:padena"
        ),
        output_name="padena_sentinel2_stack",
        grid=make_exact_grid(),
    )

    result = service.start_export(request)
    assert result == EarthEngineExportTaskReference(
        task_id="task-123"
    )
    assert provider.export_requests == [request]


def test_service_rejects_invalid_export_before_delegation() -> None:
    provider = FakeEarthEngineProvider()
    service = EarthEngineService(provider)
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(image_id=" "),
        output_name=" ",
        grid=RasterGridSpec(
            crs="EPSG:32639",
            width=512,
            height=512,
            pixel_size_x=10.0,
            pixel_size_y=10.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Invalid Earth Engine export request",
    ):
        service.start_export(request)
    assert provider.export_requests == []


def test_service_delegates_valid_task_status_request() -> None:
    status = EarthEngineExportTaskStatus(
        task_id="task-123",
        state=EarthEngineTaskState.RUNNING,
    )
    provider = FakeEarthEngineProvider(
        export_task_id="task-123",
        export_status=status,
    )
    service = EarthEngineService(provider)
    task = EarthEngineExportTaskReference(task_id="task-123")

    result = service.get_export_status(task)
    assert result == status
    assert provider.status_requests == [task]


def test_service_rejects_empty_task_id_before_delegation() -> None:
    provider = FakeEarthEngineProvider()
    service = EarthEngineService(provider)
    task = EarthEngineExportTaskReference(task_id=" ")

    with pytest.raises(
        ValueError,
        match="task_id must not be empty",
    ):
        service.get_export_status(task)
    assert provider.status_requests == []