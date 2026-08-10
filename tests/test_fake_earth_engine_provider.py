from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineProvider,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
    EarthEngineTaskState,
    FakeEarthEngineProvider,
    RasterGridSpec,
    Sentinel2CloudMaskSpec,
    EarthEngineAggregationMethod,
    EarthEngineExportDestination,
)


def make_grid() -> RasterGridSpec:
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


def test_fake_provider_satisfies_provider_protocol() -> None:
    provider = FakeEarthEngineProvider()
    assert isinstance(provider, EarthEngineProvider)


def test_fake_provider_returns_configured_scene_results() -> None:
    scenes = (
        EarthEngineSceneReference(
            scene_id="scene-1",
            acquisition_date="2024-07-10",
            cloud_cover=4.0,
        ),
        EarthEngineSceneReference(
            scene_id="scene-2",
            acquisition_date="2024-07-20",
            cloud_cover=7.5,
        ),
    )
    provider = FakeEarthEngineProvider(
        scene_results=scenes,
    )
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

    result = provider.search_sentinel2_scenes(query)
    assert result == scenes
    assert provider.scene_queries == [query]


def test_fake_provider_returns_configured_composite_reference() -> None:
    provider = FakeEarthEngineProvider(
        composite_image_id="composite:padena",
    )
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-2"),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=EarthEngineAggregationMethod.MEDIAN,
    )
    image = provider.build_composite(request)
    assert image == EarthEngineImageReference(
        image_id="composite:padena"
    )
    assert provider.composite_requests == [request]


def test_fake_provider_returns_configured_export_task() -> None:
    provider = FakeEarthEngineProvider(
        export_task_id="task-123",
    )
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:padena"
        ),
        output_name="padena_sentinel2_stack",
        grid=make_grid(),
        destination=EarthEngineExportDestination.DRIVE,
        destination_folder="geoai-dataset-curation",
    )
    task = provider.start_export(request)
    assert task == EarthEngineExportTaskReference(
        task_id="task-123"
    )
    assert provider.export_requests == [request]
    assert request.destination is EarthEngineExportDestination.DRIVE
    assert request.destination_folder == "geoai-dataset-curation"


def test_fake_provider_returns_configured_export_status() -> None:
    configured_status = EarthEngineExportTaskStatus(
        task_id="task-123",
        state=EarthEngineTaskState.FAILED,
        error_message="Simulated export failure.",
    )
    provider = FakeEarthEngineProvider(
        export_task_id="task-123",
        export_status=configured_status,
    )
    task = EarthEngineExportTaskReference(
        task_id="task-123"
    )
    status = provider.get_export_status(task)
    assert status == configured_status
    assert provider.status_requests == [task]