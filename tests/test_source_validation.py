from shapely.geometry import Point, Polygon
from geoai_dataset_curation.validation import validate_source


def test_validate_source_returns_correct_summary() -> None:
    geometries = [
        Polygon(
            [
                (0, 0),
                (2, 0),
                (2, 2),
                (0, 2),
                (0, 0),
            ]
        ),
        None,
        Point(1, 1),
    ]
    summary = validate_source(
        source_id="padena_landslides",
        geometries=geometries,
    )
    assert summary.source_id == "padena_landslides"
    assert summary.feature_count == 3
    assert summary.valid_feature_count == 1
    assert summary.invalid_feature_count == 2
    assert summary.is_valid is False


def test_validate_source_collects_issue_codes() -> None:
    geometries = [
        None,
        Point(1, 1),
    ]
    summary = validate_source(
        source_id="padena_non_landslides",
        geometries=geometries,
    )
    issue_codes = {issue.code for issue in summary.issues}
    assert issue_codes == {
        "missing_geometry",
        "unsupported_geometry_type",
    }