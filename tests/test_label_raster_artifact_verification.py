from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterArtifactSpec,
    verify_label_raster_artifact,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=10,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3500000.0,
        ),
    )


def make_metadata(
    *,
    band_count: int = 1,
    dtypes: tuple[str, ...] = ("uint8",),
    transform: Affine | None = None,
) -> RasterArtifactMetadata:
    return RasterArtifactMetadata(
        path=Path("label.tif"),
        driver="GTiff",
        crs="EPSG:32639",
        width=10,
        height=8,
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


def test_valid_label_raster_matches_contract() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )
    result = verify_label_raster_artifact(
        metadata=make_metadata(),
        observed_values=(0, 1, 255),
        spec=spec,
    )
    assert result.grid.matches is True
    assert result.band_count_matches is True
    assert result.dtype_matches is True
    assert result.values_valid is True
    assert result.matches is True


def test_unexpected_pixel_value_fails_verification() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )

    result = verify_label_raster_artifact(
        metadata=make_metadata(),
        observed_values=(0, 1, 2, 255),
        spec=spec,
    )
    assert result.values_valid is False
    assert result.matches is False


def test_wrong_dtype_fails_verification() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )

    result = verify_label_raster_artifact(
        metadata=make_metadata(
            dtypes=("float32",),
        ),
        observed_values=(0, 1, 255),
        spec=spec,
    )
    assert result.dtype_matches is False
    assert result.matches is False


def test_wrong_band_count_fails_verification() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )
    result = verify_label_raster_artifact(
        metadata=make_metadata(
            band_count=2,
            dtypes=("uint8", "uint8"),
        ),
        observed_values=(0, 1, 255),
        spec=spec,
    )
    assert result.band_count_matches is False
    assert result.dtype_matches is False
    assert result.matches is False


def test_shifted_grid_fails_verification() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )
    result = verify_label_raster_artifact(
        metadata=make_metadata(
            transform=Affine(
                10.0,
                0.0,
                500010.0,
                0.0,
                -10.0,
                3500000.0,
            ),
        ),
        observed_values=(0, 1, 255),
        spec=spec,
    )
    assert result.grid.transform_matches is False
    assert result.matches is False