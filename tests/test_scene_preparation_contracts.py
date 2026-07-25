from datetime import date
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    ScenePreparationResult,
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


def test_scene_preparation_result_stores_summary() -> None:
    candidate = SceneCandidate(
        scene_id="S2A_SELECTED_SCENE",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    result = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=3,
        selected_count=1,
        rejected_count=2,
        selected_scenes=(candidate,),
    )

    assert result.source_id == "padena_aoi"
    assert result.candidate_count == 3
    assert result.selected_count == 1
    assert result.rejected_count == 2
    assert result.selected_scenes == (candidate,)
    assert result.has_selected_scenes is True


def test_scene_preparation_result_reports_no_selected_scenes() -> None:
    result = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=2,
        selected_count=0,
        rejected_count=2,
        selected_scenes=(),
    )
    
    assert result.has_selected_scenes is False