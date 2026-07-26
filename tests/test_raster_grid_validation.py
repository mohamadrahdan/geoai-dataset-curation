from geoai_dataset_curation.image_construction import (
    RasterGridSpec,
    validate_raster_grid_spec,
)


def test_validate_raster_grid_spec_accepts_valid_grid() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    errors = validate_raster_grid_spec(grid)
    assert errors == ()


def test_validate_raster_grid_spec_rejects_empty_crs() -> None:
    grid = RasterGridSpec(
        crs=" ",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    errors = validate_raster_grid_spec(grid)
    assert "grid.crs must not be empty." in errors


def test_validate_raster_grid_spec_rejects_non_positive_dimensions() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=0,
        height=-1,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    errors = validate_raster_grid_spec(grid)

    assert "grid.width must be greater than zero." in errors
    assert "grid.height must be greater than zero." in errors


def test_validate_raster_grid_spec_rejects_non_positive_pixel_sizes() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=0.0,
        pixel_size_y=-10.0,
    )

    errors = validate_raster_grid_spec(grid)
    assert "grid.pixel_size_x must be greater than zero." in errors
    assert "grid.pixel_size_y must be greater than zero." in errors