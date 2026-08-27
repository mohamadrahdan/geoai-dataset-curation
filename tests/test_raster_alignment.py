from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.raster_alignment import (
    verify_raster_alignment,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)


def _metadata(
    *,
    path: str,
    transform: Affine,
    crs: str = "EPSG:32639",
    width: int = 97,
    height: int = 112,
) -> RasterArtifactMetadata:
    return RasterArtifactMetadata(
        path=Path(path),
        driver="GTiff",
        crs=crs,
        width=width,
        height=height,
        band_count=1,
        dtypes=("uint8",),
        transform=transform,
    )


def test_verify_raster_alignment_accepts_exact_pixel_grid() -> None:
    transform = Affine(
        10.0,
        0.0,
        547020.0,
        0.0,
        -10.0,
        3374300.0,
    )
    reference = _metadata(
        path="image.tif",
        transform=transform,
    )
    candidate = _metadata(
        path="mask.tif",
        transform=transform,
    )
    result = verify_raster_alignment(
        reference,
        candidate,
    )
    assert result.crs_matches is True
    assert result.width_matches is True
    assert result.height_matches is True
    assert result.transform_matches is True
    assert result.aligned is True


def test_verify_raster_alignment_detects_half_pixel_shift() -> None:
    reference = _metadata(
        path="image.tif",
        transform=Affine(
            10.0,
            0.0,
            547020.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )
    candidate = _metadata(
        path="mask.tif",
        transform=Affine(
            10.0,
            0.0,
            547025.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )
    result = verify_raster_alignment(
        reference,
        candidate,
    )
    assert result.crs_matches is True
    assert result.width_matches is True
    assert result.height_matches is True
    assert result.transform_matches is False
    assert result.aligned is False


def test_verify_raster_alignment_detects_crs_mismatch() -> None:
    transform = Affine(
        10.0,
        0.0,
        547020.0,
        0.0,
        -10.0,
        3374300.0,
    )
    reference = _metadata(
        path="image.tif",
        transform=transform,
    )
    candidate = _metadata(
        path="mask.tif",
        transform=transform,
        crs="EPSG:32638",
    )
    result = verify_raster_alignment(
        reference,
        candidate,
    )
    assert result.crs_matches is False
    assert result.transform_matches is True
    assert result.aligned is False