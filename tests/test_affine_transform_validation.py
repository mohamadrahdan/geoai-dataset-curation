from math import inf, nan
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    validate_affine_transform_spec,
)


def test_validate_affine_transform_spec_accepts_valid_north_up_transform() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=3600000.0,
    )

    errors = validate_affine_transform_spec(
        transform,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert errors == ()


def test_validate_affine_transform_spec_rejects_non_finite_coefficients() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=nan,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=inf,
    )

    errors = validate_affine_transform_spec(
        transform,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert "grid.transform coefficients must be finite." in errors


def test_validate_affine_transform_spec_rejects_zero_scale_coefficients() -> None:
    transform = AffineTransformSpec(
        a=0.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=0.0,
        f=3600000.0,
    )

    errors = validate_affine_transform_spec(
        transform,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert "grid.transform.a must not be zero." in errors
    assert "grid.transform.e must not be zero." in errors


def test_validate_affine_transform_spec_rejects_rotation_and_shear() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.5,
        c=500000.0,
        d=-0.5,
        e=-10.0,
        f=3600000.0,
    )

    errors = validate_affine_transform_spec(
        transform,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert (
        "grid.transform.b must be zero for a north-up raster grid."
        in errors
    )
    assert (
        "grid.transform.d must be zero for a north-up raster grid."
        in errors
    )


def test_validate_affine_transform_spec_rejects_pixel_size_mismatch() -> None:
    transform = AffineTransformSpec(
        a=20.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-30.0,
        f=3600000.0,
    )

    errors = validate_affine_transform_spec(
        transform,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert "grid.transform.a must match grid.pixel_size_x." in errors
    assert "grid.transform.e must match grid.pixel_size_y." in errors