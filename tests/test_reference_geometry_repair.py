import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.label_rasterization.geometry_repair import (
    repair_invalid_reference_geometries,
)


def make_self_intersecting_polygon() -> Polygon:
    return Polygon(
        [
            (0.0, 0.0),
            (2.0, 2.0),
            (0.0, 2.0),
            (2.0, 0.0),
            (0.0, 0.0),
        ]
    )


def make_valid_polygon() -> Polygon:
    return Polygon(
        [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0),
            (0.0, 0.0),
        ]
    )


def test_invalid_polygon_is_repaired() -> None:
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                make_self_intersecting_polygon(),
            ]
        },
        crs="EPSG:4326",
    )
    repaired, summary = repair_invalid_reference_geometries(frame)
    assert repaired.geometry.iloc[0].is_valid is True
    assert repaired.geometry.iloc[0].geom_type in {
        "Polygon",
        "MultiPolygon",
    }
    assert summary.feature_count == 1
    assert summary.repaired_count == 1
    assert summary.unchanged_count == 0


def test_valid_polygon_is_not_modified() -> None:
    polygon = make_valid_polygon()
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                polygon,
            ]
        },
        crs="EPSG:4326",
    )
    repaired, summary = repair_invalid_reference_geometries(frame)
    assert repaired.geometry.iloc[0].equals(polygon)
    assert summary.repaired_count == 0
    assert summary.unchanged_count == 1


def test_mixed_source_repairs_only_invalid_features() -> None:
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                make_valid_polygon(),
                make_self_intersecting_polygon(),
            ]
        },
        crs="EPSG:4326",
    )
    repaired, summary = repair_invalid_reference_geometries(frame)
    assert repaired.geometry.is_valid.all()
    assert summary.feature_count == 2
    assert summary.repaired_count == 1
    assert summary.unchanged_count == 1