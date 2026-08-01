from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    RasterGridSpec,
    validate_exact_raster_grid_spec,
)


def make_grid(
    *,
    transform: AffineTransformSpec | None,
) -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=transform,
    )


def test_validate_exact_raster_grid_spec_accepts_valid_grid() -> None:
    grid = make_grid(
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        )
    )

    errors = validate_exact_raster_grid_spec(grid)

    assert errors == ()


def test_validate_exact_raster_grid_spec_requires_transform() -> None:
    grid = make_grid(transform=None)

    errors = validate_exact_raster_grid_spec(grid)

    assert (
        "grid.transform is required for exact raster export."
        in errors
    )


def test_validate_exact_raster_grid_spec_requires_positive_x_scale() -> None:
    grid = make_grid(
        transform=AffineTransformSpec(
            a=-10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        )
    )

    errors = validate_exact_raster_grid_spec(grid)

    assert (
        "grid.transform.a must be positive for a north-up raster grid."
        in errors
    )


def test_validate_exact_raster_grid_spec_requires_negative_y_scale() -> None:
    grid = make_grid(
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=10.0,
            f=3600000.0,
        )
    )

    errors = validate_exact_raster_grid_spec(grid)

    assert (
        "grid.transform.e must be negative for a north-up raster grid."
        in errors
    )


def test_validate_exact_raster_grid_spec_includes_generic_grid_errors() -> None:
    grid = RasterGridSpec(
        crs=" ",
        width=0,
        height=-1,
        pixel_size_x=0.0,
        pixel_size_y=-10.0,
        transform=None,
    )

    errors = validate_exact_raster_grid_spec(grid)

    assert "grid.crs must not be empty." in errors
    assert "grid.width must be greater than zero." in errors
    assert "grid.height must be greater than zero." in errors
    assert "grid.pixel_size_x must be greater than zero." in errors
    assert "grid.pixel_size_y must be greater than zero." in errors
    assert (
        "grid.transform is required for exact raster export."
        in errors
    )