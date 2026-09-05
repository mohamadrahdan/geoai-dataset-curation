from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from geoai_dataset_curation.label_rasterization import (
    verify_raster_pair_alignment,
)


def make_metadata(
    *,
    path: str,
    crs: str = "EPSG:32639",
    width: int = 10,
    height: int = 8,
    transform: Affine | None = None,
    band_count: int = 1,
    dtypes: tuple[str, ...] = ("uint8",),
) -> RasterArtifactMetadata:
    return RasterArtifactMetadata(
        path=Path(path),
        driver="GTiff",
        crs=crs,
        width=width,
        height=height,
        band_count=band_count,
        dtypes=dtypes,
        transform=transform
        or Affine(
            10.0,
            0.0,
            500000.0,
            0.0,
            -10.0,
            3500000.0,
        ),
    )


def test_exact_image_label_alignment_passes() -> None:
    image = make_metadata(
        path="image.tif",
        band_count=4,
        dtypes=("float64",) * 4,
    )
    label = make_metadata(
        path="label.tif",
    )
    result = verify_raster_pair_alignment(
        image=image,
        label=label,
    )
    assert result.crs_matches is True
    assert result.width_matches is True
    assert result.height_matches is True
    assert result.transform_matches is True
    assert result.matches is True


def test_one_pixel_origin_shift_fails_alignment() -> None:
    image = make_metadata(
        path="image.tif",
        band_count=4,
        dtypes=("float64",) * 4,
    )
    label = make_metadata(
        path="label.tif",
        transform=Affine(
            10.0,
            0.0,
            500010.0,
            0.0,
            -10.0,
            3500000.0,
        ),
    )
    result = verify_raster_pair_alignment(
        image=image,
        label=label,
    )
    assert result.transform_matches is False
    assert result.matches is False


def test_width_mismatch_fails_alignment() -> None:
    image = make_metadata(
        path="image.tif",
        width=10,
        band_count=4,
        dtypes=("float64",) * 4,
    )
    label = make_metadata(
        path="label.tif",
        width=9,
    )
    result = verify_raster_pair_alignment(
        image=image,
        label=label,
    )
    assert result.width_matches is False
    assert result.matches is False


def test_crs_mismatch_fails_alignment() -> None:
    image = make_metadata(
        path="image.tif",
        crs="EPSG:32639",
        band_count=4,
        dtypes=("float64",) * 4,
    )
    label = make_metadata(
        path="label.tif",
        crs="EPSG:4326",
    )
    result = verify_raster_pair_alignment(
        image=image,
        label=label,
    )
    assert result.crs_matches is False
    assert result.matches is False