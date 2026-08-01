import pytest
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    RasterBounds,
    RasterGridSpec,
    derive_raster_bounds,
)


def test_raster_bounds_returns_expected_tuple_order() -> None:
    bounds = RasterBounds(
        left=500000.0,
        bottom=3594880.0,
        right=505120.0,
        top=3600000.0,
    )

    assert bounds.as_tuple == (
        500000.0,
        3594880.0,
        505120.0,
        3600000.0,
    )


def test_derive_raster_bounds_from_exact_grid() -> None:
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

    bounds = derive_raster_bounds(grid)
    assert bounds == RasterBounds(
        left=500000.0,
        bottom=3594880.0,
        right=505120.0,
        top=3600000.0,
    )


def test_derive_raster_bounds_rejects_grid_without_transform() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    with pytest.raises(
        ValueError,
        match="grid.transform is required for exact raster export",
    ):
        derive_raster_bounds(grid)


def test_derive_raster_bounds_rejects_invalid_orientation() -> None:
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
            e=10.0,
            f=3600000.0,
        ),
    )
    with pytest.raises(
        ValueError,
        match="grid.transform.e must be negative",
    ):
        derive_raster_bounds(grid)