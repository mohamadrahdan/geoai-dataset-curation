import pytest
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    RasterGridSpec,
    raster_grid_to_earth_engine_export_params,
)


def test_raster_grid_to_earth_engine_export_params_serializes_exact_grid() -> None:
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

    params = raster_grid_to_earth_engine_export_params(grid)

    assert params == {
        "crs": "EPSG:32639",
        "crsTransform": [
            10.0,
            0.0,
            500000.0,
            0.0,
            -10.0,
            3600000.0,
        ],
        "dimensions": {
            "width": 512,
            "height": 512,
        },
        "bounds": {
            "left": 500000.0,
            "bottom": 3594880.0,
            "right": 505120.0,
            "top": 3600000.0,
        },
    }


def test_raster_grid_to_earth_engine_export_params_rejects_missing_transform() -> None:
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
        raster_grid_to_earth_engine_export_params(grid)


def test_raster_grid_to_earth_engine_export_params_rejects_invalid_orientation() -> None:
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
        raster_grid_to_earth_engine_export_params(grid)