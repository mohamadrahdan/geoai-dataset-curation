from datetime import date
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    SceneSelectionRequest,
)


def test_scene_selection_request_stores_selection_criteria() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )

    assert request.source_id == "padena_aoi"
    assert request.start_date == date(2024, 1, 1)
    assert request.end_date == date(2024, 12, 31)
    assert request.collection == "COPERNICUS/S2_SR_HARMONIZED"
    assert request.required_bands == ("B2", "B3", "B4", "B8")
    assert request.max_cloud_cover == 20.0


def test_scene_candidate_stores_scene_metadata() -> None:
    candidate = SceneCandidate(
        scene_id="S2A_SAMPLE_SCENE",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    assert candidate.scene_id == "S2A_SAMPLE_SCENE"
    assert candidate.acquisition_date == date(2024, 5, 18)
    assert candidate.cloud_cover == 8.5
    assert candidate.collection == "COPERNICUS/S2_SR_HARMONIZED"
    assert candidate.available_bands == ("B2", "B3", "B4", "B8")