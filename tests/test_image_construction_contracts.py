from geoai_dataset_curation.image_construction import (
    ImageConstructionRequest,
    ImageConstructionResult,
    RasterGridSpec,
)


def test_raster_grid_spec_stores_target_grid_definition() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert grid.crs == "EPSG:32639"
    assert grid.width == 512
    assert grid.height == 512
    assert grid.pixel_size_x == 10.0
    assert grid.pixel_size_y == 10.0


def test_image_construction_request_stores_input_contract() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    request = ImageConstructionRequest(
        source_id="padena_aoi",
        scene_ids=("S2A_SCENE_001", "S2B_SCENE_002"),
        bands=("B2", "B3", "B4", "B8"),
        grid=grid,
        output_name="padena_sentinel2_stack",
    )

    assert request.source_id == "padena_aoi"
    assert request.scene_ids == (
        "S2A_SCENE_001",
        "S2B_SCENE_002",
    )
    assert request.bands == ("B2", "B3", "B4", "B8")
    assert request.grid == grid
    assert request.output_name == "padena_sentinel2_stack"


def test_image_construction_result_stores_run_summary() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    result = ImageConstructionResult(
        source_id="padena_aoi",
        output_name="padena_sentinel2_stack",
        scene_count=2,
        band_count=4,
        grid=grid,
        artifact_uri="artifacts/padena_sentinel2_stack.tif",
    )

    assert result.source_id == "padena_aoi"
    assert result.output_name == "padena_sentinel2_stack"
    assert result.scene_count == 2
    assert result.band_count == 4
    assert result.grid == grid
    assert result.artifact_uri == "artifacts/padena_sentinel2_stack.tif"
    assert result.has_artifact is True


def test_image_construction_result_reports_missing_artifact() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    result = ImageConstructionResult(
        source_id="padena_aoi",
        output_name="padena_sentinel2_stack",
        scene_count=2,
        band_count=4,
        grid=grid,
        artifact_uri=" ",
    )

    assert result.has_artifact is False