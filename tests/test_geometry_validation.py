from shapely.geometry import Point, Polygon
from geoai_dataset_curation.validation import validate_geometry


def test_valid_polygon_has_no_issues() -> None:
    polygon = Polygon(
        [
            (0, 0),
            (2, 0),
            (2, 2),
            (0, 2),
            (0, 0),
        ]
    )

    issues = validate_geometry(polygon, feature_index=0)
    assert issues == ()


def test_missing_geometry_is_reported() -> None:
    issues = validate_geometry(None, feature_index=1)

    assert len(issues) == 1
    assert issues[0].code == "missing_geometry"
    assert issues[0].feature_index == 1


def test_empty_geometry_is_reported() -> None:
    issues = validate_geometry(Polygon(), feature_index=2)
    assert any(issue.code == "empty_geometry" for issue in issues)


def test_unsupported_geometry_type_is_reported() -> None:
    issues = validate_geometry(Point(1, 1), feature_index=3)
    assert any(
        issue.code == "unsupported_geometry_type"
        for issue in issues
    )


def test_invalid_polygon_is_reported() -> None:
    self_intersecting_polygon = Polygon(
        [
            (0, 0),
            (2, 2),
            (2, 0),
            (0, 2),
            (0, 0),
        ]
    )

    issues = validate_geometry(
        self_intersecting_polygon,
        feature_index=4,
    )
    assert any(issue.code == "invalid_geometry" for issue in issues)