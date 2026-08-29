from shapely.geometry import box

from geoai_dataset_curation.image_construction.runtime_grid import (
    build_exact_raster_grid_from_study_area,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    StudyAreaSpec,
)


def test_build_exact_raster_grid_covers_study_area() -> None:
    study_area = StudyAreaSpec(
        study_area_id="test-area",
        source_id="test-source",
        crs="EPSG:32639",
        geometry=box(
            500003.0,
            3594877.0,
            505117.0,
            3599997.0,
        ),
    )

    grid = build_exact_raster_grid_from_study_area(
        study_area=study_area,
        target_crs="EPSG:32639",
        pixel_size=10.0,
    )

    assert grid.crs == "EPSG:32639"
    assert grid.pixel_size_x == 10.0
    assert grid.pixel_size_y == 10.0
    assert grid.width == 512
    assert grid.height == 513

    assert grid.transform is not None
    assert grid.transform.as_tuple == (
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    )


def test_build_exact_raster_grid_rejects_invalid_pixel_size() -> None:
    study_area = StudyAreaSpec(
        study_area_id="test-area",
        source_id="test-source",
        crs="EPSG:32639",
        geometry=box(
            500000.0,
            3595000.0,
            505000.0,
            3600000.0,
        ),
    )

    try:
        build_exact_raster_grid_from_study_area(
            study_area=study_area,
            target_crs="EPSG:32639",
            pixel_size=0.0,
        )
    except ValueError as error:
        assert (
            str(error)
            == "pixel_size must be greater than zero."
        )
    else:
        raise AssertionError(
            "Expected ValueError for invalid pixel size."
        )