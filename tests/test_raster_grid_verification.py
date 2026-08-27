from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from geoai_dataset_curation.image_construction.raster_grid_verification import (
    verify_raster_against_grid,
)


def test_verify_raster_against_grid_accepts_exact_match() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=97,
        height=112,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=547020.0,
            d=0.0,
            e=-10.0,
            f=3374300.0,
        ),
    )
    metadata = RasterArtifactMetadata(
        path=Path("example.tif"),
        driver="GTiff",
        crs="EPSG:32639",
        width=97,
        height=112,
        band_count=4,
        dtypes=(
            "float64",
            "float64",
            "float64",
            "float64",
        ),
        transform=Affine(
            10.0,
            0.0,
            547020.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )
    result = verify_raster_against_grid(
        metadata,
        grid,
    )
    assert result.crs_matches is True
    assert result.width_matches is True
    assert result.height_matches is True
    assert result.transform_matches is True
    assert result.matches is True


def test_verify_raster_against_grid_detects_transform_mismatch() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=97,
        height=112,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=547020.0,
            d=0.0,
            e=-10.0,
            f=3374300.0,
        ),
    )
    metadata = RasterArtifactMetadata(
        path=Path("example.tif"),
        driver="GTiff",
        crs="EPSG:32639",
        width=97,
        height=112,
        band_count=4,
        dtypes=("float64",) * 4,
        transform=Affine(
            10.0,
            0.0,
            547030.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )
    result = verify_raster_against_grid(
        metadata,
        grid,
    )
    assert result.crs_matches is True
    assert result.width_matches is True
    assert result.height_matches is True
    assert result.transform_matches is False
    assert result.matches is False