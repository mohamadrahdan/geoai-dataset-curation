from pathlib import Path
import geopandas as gpd
import pytest
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon
from geoai_dataset_curation.scene_preparation import (
    StudyAreaLoadingError,
    load_study_area,
)


def _polygon(
    left: float,
    bottom: float,
    right: float,
    top: float,
) -> Polygon:
    return Polygon(
        [
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top),
            (left, bottom),
        ]
    )


def test_load_study_area_builds_contract_from_one_feature() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[
            _polygon(51.0, 30.0, 51.2, 30.2),
        ],
        crs="EPSG:4326",
    )

    def reader(path: Path) -> gpd.GeoDataFrame:
        assert path == Path("inputs/study-area.geojson")
        return frame

    study_area = load_study_area(
        path="inputs/study-area.geojson",
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        reader=reader,
    )
    assert study_area.study_area_id == "study-area-loop-1"
    assert study_area.source_id == "validated-boundary-source"
    assert study_area.crs == "EPSG:4326"
    #assert study_area.geometry.equals(frame.geometry.iloc[0])
    expected_geometry = frame.geometry.iloc[0]
    assert isinstance(expected_geometry, BaseGeometry)
    assert study_area.geometry.equals(expected_geometry)


def test_load_study_area_combines_multiple_features() -> None:
    first = _polygon(51.0, 30.0, 51.1, 30.1)
    second = _polygon(51.2, 30.2, 51.3, 30.3)

    frame = gpd.GeoDataFrame(
        geometry=[
            first,
            second,
        ],
        crs="EPSG:4326",
    )

    study_area = load_study_area(
        path="inputs/study-area.gpkg",
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        reader=lambda path: frame,
    )
    assert study_area.geometry.geom_type == "MultiPolygon"
    assert study_area.geometry.equals(
        frame.geometry.union_all()
    )


def test_load_study_area_preserves_projected_crs() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[
            _polygon(500000.0, 3300000.0, 501000.0, 3301000.0),
        ],
        crs="EPSG:32639",
    )

    study_area = load_study_area(
        path="inputs/study-area.gpkg",
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        reader=lambda path: frame,
    )
    assert study_area.crs == "EPSG:32639"


def test_load_study_area_preserves_missing_crs_for_validation() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[
            _polygon(51.0, 30.0, 51.2, 30.2),
        ],
    )

    study_area = load_study_area(
        path="inputs/study-area.geojson",
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        reader=lambda path: frame,
    )
    assert study_area.crs == ""


def test_load_study_area_rejects_empty_source() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[],
        crs="EPSG:4326",
    )

    with pytest.raises(
        StudyAreaLoadingError,
        match="must contain at least one feature",
    ):
        load_study_area(
            path="inputs/empty.geojson",
            study_area_id="study-area-loop-1",
            source_id="validated-boundary-source",
            reader=lambda path: frame,
        )


def test_load_study_area_normalizes_reader_failure() -> None:
    def failing_reader(path: Path) -> gpd.GeoDataFrame:
        raise OSError("source not found")

    with pytest.raises(
        StudyAreaLoadingError,
        match="Study-area source could not be loaded",
    ):
        load_study_area(
            path="inputs/missing.geojson",
            study_area_id="study-area-loop-1",
            source_id="validated-boundary-source",
            reader=failing_reader,
        )