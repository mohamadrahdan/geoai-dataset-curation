from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterArtifactSpec,
    validate_label_raster_artifact_spec,
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


def test_loop1_label_artifact_spec_is_valid() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
    )
    assert validate_label_raster_artifact_spec(spec) == ()


def test_multiband_label_artifact_is_rejected() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
        band_count=2,
    )
    assert (
        "band_count must be exactly 1."
        in validate_label_raster_artifact_spec(spec)
    )


def test_non_uint8_label_artifact_is_rejected() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
        dtype="float32",
    )
    assert (
        "dtype must be uint8."
        in validate_label_raster_artifact_spec(spec)
    )


def test_unexpected_allowed_values_are_rejected() -> None:
    spec = LabelRasterArtifactSpec(
        output_name="label-raster",
        grid=make_grid(),
        allowed_values=(0, 1, 2, 255),
    )
    assert (
        "allowed_values must match the Loop 1 label values."
        in validate_label_raster_artifact_spec(spec)
    )