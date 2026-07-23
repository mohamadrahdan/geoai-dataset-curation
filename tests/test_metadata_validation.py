import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.validation import validate_source_metadata


def test_validate_source_metadata_accepts_non_empty_source_with_crs() -> None:
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon(
                    [
                        (0, 0),
                        (1, 0),
                        (1, 1),
                        (0, 1),
                        (0, 0),
                    ]
                )
            ]
        },
        crs="EPSG:4326",
    )

    issues = validate_source_metadata(frame)
    assert issues == ()


def test_validate_source_metadata_reports_empty_source() -> None:
    frame = gpd.GeoDataFrame(
        {"geometry": []},
        geometry="geometry",
        crs="EPSG:4326",
    )

    issues = validate_source_metadata(frame)
    assert len(issues) == 1
    assert issues[0].code == "empty_source"


def test_validate_source_metadata_reports_missing_crs() -> None:
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon(
                    [
                        (0, 0),
                        (1, 0),
                        (1, 1),
                        (0, 1),
                        (0, 0),
                    ]
                )
            ]
        }
    )

    issues = validate_source_metadata(frame)
    assert len(issues) == 1
    assert issues[0].code == "missing_crs"


def test_validate_source_metadata_reports_all_detected_issues() -> None:
    frame = gpd.GeoDataFrame(
        {"geometry": []},
        geometry="geometry",
    )

    issues = validate_source_metadata(frame)
    assert [issue.code for issue in issues] == [
        "empty_source",
        "missing_crs",
    ]