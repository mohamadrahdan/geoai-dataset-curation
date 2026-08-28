from datetime import date
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.image_construction.runtime_input import (
    RealImageRuntimeInput,
    build_real_image_runtime_input,
)
import pytest

from geoai_dataset_curation.scene_preparation.study_area_loading import (
    StudyAreaLoadingError,
)


def test_build_real_image_runtime_input_wires_real_study_area(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "study_area.geojson"
    frame = gpd.GeoDataFrame(
        {"id": [1],},
        geometry=[
            Polygon(
                [
                    (51.0, 30.0),
                    (51.2, 30.0),
                    (51.2, 30.2),
                    (51.0, 30.2),
                    (51.0, 30.0),
                ]
            )
        ],
        crs="EPSG:4326",
    )

    frame.to_file(
        source_path,
        driver="GeoJSON",
    )

    runtime_input = build_real_image_runtime_input(
        study_area_path=source_path,
        study_area_id="study-area-loop-1",
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        max_cloud_cover=20.0,
    )

    assert isinstance(runtime_input, RealImageRuntimeInput,)
    assert (runtime_input.study_area.source_id == "padena_aoi")
    assert (runtime_input.study_area.crs == "EPSG:4326")
    assert (runtime_input.selection_request.required_bands
        == (
            "B2",
            "B3",
            "B4",
            "B8",
        )
    )
    assert (runtime_input.scene_query.collection_id
        == "COPERNICUS/S2_SR_HARMONIZED"
    )
    assert (runtime_input.scene_query.start_date == "2024-01-01")
    assert (runtime_input.scene_query.end_date == "2024-12-31")
    assert (runtime_input.scene_query.maximum_cloud_cover == 20.0)
    assert (runtime_input.scene_query.aoi_geojson["type"] == "Polygon")


def test_build_real_image_runtime_input_rejects_missing_study_area(
    tmp_path: Path,
) -> None:
    missing_path = (
        tmp_path
        / "missing-study-area.geojson"
    )

    with pytest.raises(
        StudyAreaLoadingError,
        match="could not be loaded",
    ):
        build_real_image_runtime_input(
            study_area_path=missing_path,
            study_area_id="study-area-loop-1",
            source_id="padena_aoi",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            collection=(
                "COPERNICUS/S2_SR_HARMONIZED"
            ),
            required_bands=(
                "B2",
                "B3",
                "B4",
                "B8",
            ),
            max_cloud_cover=20.0,
        )