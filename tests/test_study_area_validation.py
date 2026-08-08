from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiPolygon,
    Polygon,
)
from geoai_dataset_curation.scene_preparation import (
    StudyAreaSpec,
    validate_study_area,
)


def _valid_polygon() -> Polygon:
    return Polygon(
        [
            (51.0, 30.0),
            (51.2, 30.0),
            (51.2, 30.2),
            (51.0, 30.2),
            (51.0, 30.0),
        ]
    )


def test_validate_study_area_accepts_valid_polygon() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=_valid_polygon(),
    )
    errors = validate_study_area(study_area)
    assert errors == ()


def test_validate_study_area_accepts_valid_multipolygon() -> None:
    geometry = MultiPolygon(
        [
            _valid_polygon(),
            Polygon(
                [
                    (51.3, 30.3),
                    (51.4, 30.3),
                    (51.4, 30.4),
                    (51.3, 30.4),
                    (51.3, 30.3),
                ]
            ),
        ]
    )
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=geometry,
    )
    errors = validate_study_area(study_area)
    assert errors == ()


def test_validate_study_area_rejects_empty_identifiers_and_crs() -> None:
    study_area = StudyAreaSpec(
        study_area_id=" ",
        source_id="",
        crs=" ",
        geometry=_valid_polygon(),
    )
    errors = validate_study_area(study_area)
    assert "study_area_id must not be empty" in errors
    assert "source_id must not be empty" in errors
    assert "crs must not be empty" in errors


def test_validate_study_area_rejects_empty_geometry() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=GeometryCollection(),
    )
    errors = validate_study_area(study_area)
    assert "geometry must not be empty" in errors
    assert (
        "geometry must be a Polygon or MultiPolygon"
        in errors
    )


def test_validate_study_area_rejects_non_polygon_geometry() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=LineString(
            [
                (51.0, 30.0),
                (51.2, 30.2),
            ]
        ),
    )
    errors = validate_study_area(study_area)
    assert (
        "geometry must be a Polygon or MultiPolygon"
        in errors
    )


def test_validate_study_area_rejects_invalid_polygon() -> None:
    invalid_geometry = Polygon(
        [
            (51.0, 30.0),
            (51.2, 30.2),
            (51.2, 30.0),
            (51.0, 30.2),
            (51.0, 30.0),
        ]
    )
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=invalid_geometry,
    )
    errors = validate_study_area(study_area)
    assert "geometry must be valid" in errors