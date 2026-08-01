from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    RasterGridSpec,
    build_raster_grid_id,
    raster_grid_identity_payload,
    raster_grids_match,
)


def make_grid(
    *,
    crs: str = "EPSG:32639",
    origin_x: float = 500000.0,
    origin_y: float = 3600000.0,
) -> RasterGridSpec:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=origin_x,
        d=0.0,
        e=-10.0,
        f=origin_y,
    )

    return RasterGridSpec(
        crs=crs,
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=transform,
    )


def test_raster_grid_identity_payload_contains_complete_grid() -> None:
    grid = make_grid()

    payload = raster_grid_identity_payload(grid)

    assert payload == {
        "schema_version": "raster-grid-v1",
        "crs": "EPSG:32639",
        "width": 512,
        "height": 512,
        "pixel_size_x": 10.0,
        "pixel_size_y": 10.0,
        "transform": [
            10.0,
            0.0,
            500000.0,
            0.0,
            -10.0,
            3600000.0,
        ],
    }


def test_build_raster_grid_id_is_stable_for_identical_grids() -> None:
    first = make_grid()
    second = make_grid()

    first_id = build_raster_grid_id(first)
    second_id = build_raster_grid_id(second)

    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_raster_grid_id_changes_when_origin_moves_by_one_pixel() -> None:
    first = make_grid(origin_x=500000.0)
    shifted = make_grid(origin_x=500010.0)

    assert build_raster_grid_id(first) != build_raster_grid_id(shifted)
    assert raster_grids_match(first, shifted) is False


def test_raster_grid_id_changes_when_crs_changes() -> None:
    first = make_grid(crs="EPSG:32639")
    second = make_grid(crs="EPSG:4326")

    assert build_raster_grid_id(first) != build_raster_grid_id(second)
    assert raster_grids_match(first, second) is False


def test_raster_grids_match_accepts_equivalent_exact_grids() -> None:
    first = make_grid()
    second = make_grid()

    assert raster_grids_match(first, second) is True


def test_legacy_grid_without_transform_has_stable_identity() -> None:
    first = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )
    second = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    assert build_raster_grid_id(first) == build_raster_grid_id(second)
    assert raster_grids_match(first, second) is True