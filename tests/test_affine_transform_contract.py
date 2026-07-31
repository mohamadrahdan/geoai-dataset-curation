from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    RasterGridSpec,
)


def test_affine_transform_spec_stores_exact_coefficients() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=3600000.0,
    )

    assert transform.a == 10.0
    assert transform.b == 0.0
    assert transform.c == 500000.0
    assert transform.d == 0.0
    assert transform.e == -10.0
    assert transform.f == 3600000.0


def test_affine_transform_spec_returns_expected_tuple_order() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=3600000.0,
    )

    assert transform.as_tuple == (
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    )


def test_raster_grid_spec_accepts_exact_affine_transform() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=3600000.0,
    )
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=transform,
    )

    assert grid.transform == transform
    assert grid.transform is not None
    assert grid.transform.as_tuple == (
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    )


def test_raster_grid_spec_remains_backward_compatible_without_transform() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert grid.transform is None