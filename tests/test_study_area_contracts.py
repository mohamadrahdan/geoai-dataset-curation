from dataclasses import FrozenInstanceError
import pytest
from shapely.geometry import MultiPolygon, Polygon
from geoai_dataset_curation.scene_preparation import StudyAreaSpec


def test_study_area_spec_stores_polygon_geometry() -> None:
    geometry = Polygon(
        [
            (51.0, 30.0),
            (51.2, 30.0),
            (51.2, 30.2),
            (51.0, 30.2),
            (51.0, 30.0),
        ]
    )

    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=geometry,
    )

    assert study_area.study_area_id == "study-area-loop-1"
    assert study_area.source_id == "validated-boundary-source"
    assert study_area.crs == "EPSG:4326"
    assert study_area.geometry.equals(geometry)


def test_study_area_spec_stores_multipolygon_geometry() -> None:
    first_polygon = Polygon(
        [
            (51.0, 30.0),
            (51.1, 30.0),
            (51.1, 30.1),
            (51.0, 30.1),
            (51.0, 30.0),
        ]
    )
    second_polygon = Polygon(
        [
            (51.2, 30.2),
            (51.3, 30.2),
            (51.3, 30.3),
            (51.2, 30.3),
            (51.2, 30.2),
        ]
    )
    geometry = MultiPolygon(
        [
            first_polygon,
            second_polygon,
        ]
    )

    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=geometry,
    )

    assert study_area.geometry.geom_type == "MultiPolygon"
    assert study_area.geometry.equals(geometry)


def test_study_area_spec_is_immutable() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=Polygon(
            [
                (51.0, 30.0),
                (51.1, 30.0),
                (51.1, 30.1),
                (51.0, 30.1),
                (51.0, 30.0),
            ]
        ),
    )

    with pytest.raises(FrozenInstanceError):
        setattr(study_area, "crs", "EPSG:32639")