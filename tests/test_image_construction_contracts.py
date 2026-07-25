from geoai_dataset_curation.image_construction import (
    ImageConstructionRequest,
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