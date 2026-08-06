from datetime import date
import pytest
from shapely.geometry import Polygon
from geoai_dataset_curation.scene_preparation import (
    EARTH_ENGINE_QUERY_CRS,
    SceneSelectionRequest,
    StudyAreaSpec,
    build_sentinel2_scene_query,
)


def _geographic_study_area() -> StudyAreaSpec:
    return StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=Polygon(
            [
                (51.0, 30.0),
                (51.2, 30.0),
                (51.2, 30.2),
                (51.0, 30.2),
                (51.0, 30.0),
            ]
        ),
    )


def _selection_request() -> SceneSelectionRequest:
    return SceneSelectionRequest(
        source_id="validated-boundary-source",
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B02", "B03", "B04", "B08"),
        max_cloud_cover=20.0,
    )


def test_build_sentinel2_scene_query_maps_selection_criteria() -> None:
    query = build_sentinel2_scene_query(
        study_area=_geographic_study_area(),
        request=_selection_request(),
    )
    assert query.collection_id == (
        "COPERNICUS/S2_SR_HARMONIZED"
    )
    assert query.start_date == "2024-04-01"
    assert query.end_date == "2024-06-30"
    assert query.maximum_cloud_cover == 20.0


def test_build_sentinel2_scene_query_creates_polygon_geojson() -> None:
    query = build_sentinel2_scene_query(
        study_area=_geographic_study_area(),
        request=_selection_request(),
    )
    assert query.aoi_geojson["type"] == "Polygon"
    assert "coordinates" in query.aoi_geojson


def test_build_sentinel2_scene_query_transforms_projected_geometry() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:32639",
        geometry=Polygon(
            [
                (500000.0, 3300000.0),
                (501000.0, 3300000.0),
                (501000.0, 3301000.0),
                (500000.0, 3301000.0),
                (500000.0, 3300000.0),
            ]
        ),
    )
    query = build_sentinel2_scene_query(
        study_area=study_area,
        request=_selection_request(),
    )
    coordinates = query.aoi_geojson["coordinates"]
    assert EARTH_ENGINE_QUERY_CRS == "EPSG:4326"
    assert coordinates is not None
    assert query.aoi_geojson["type"] == "Polygon"


def test_build_sentinel2_scene_query_rejects_source_mismatch() -> None:
    request = SceneSelectionRequest(
        source_id="different-source",
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B02", "B03", "B04", "B08"),
        max_cloud_cover=20.0,
    )
    with pytest.raises(
        ValueError,
        match=(
            "request.source_id must match "
            "study_area.source_id"
        ),
    ):
        build_sentinel2_scene_query(
            study_area=_geographic_study_area(),
            request=request,
        )


def test_build_sentinel2_scene_query_validates_study_area() -> None:
    invalid_study_area = StudyAreaSpec(
        study_area_id="",
        source_id="validated-boundary-source",
        crs="",
        geometry=Polygon(),
    )
    with pytest.raises(
        ValueError,
        match="Cannot build Sentinel-2 scene query",
    ):
        build_sentinel2_scene_query(
            study_area=invalid_study_area,
            request=_selection_request(),
        )


def test_build_sentinel2_scene_query_validates_selection_request() -> None:
    invalid_request = SceneSelectionRequest(
        source_id="validated-boundary-source",
        start_date=date(2024, 7, 1),
        end_date=date(2024, 6, 30),
        collection="",
        required_bands=(),
        max_cloud_cover=120.0,
    )

    with pytest.raises(
        ValueError,
        match="Cannot build Sentinel-2 scene query",
    ):
        build_sentinel2_scene_query(
            study_area=_geographic_study_area(),
            request=invalid_request,
        )