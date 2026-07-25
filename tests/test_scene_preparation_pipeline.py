from datetime import date
import pytest
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    SceneSelectionRequest,
    prepare_scenes,
)


def test_prepare_scenes_returns_selection_summary() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    matching_candidate = SceneCandidate(
        scene_id="S2A_MATCHING_SCENE",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8", "B11"),
    )
    rejected_candidate = SceneCandidate(
        scene_id="S2A_CLOUDY_SCENE",
        acquisition_date=date(2024, 6, 10),
        cloud_cover=35.0,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    result = prepare_scenes(
        request=request,
        candidates=[
            matching_candidate,
            rejected_candidate,
        ],
    )

    assert result.source_id == "padena_aoi"
    assert result.candidate_count == 2
    assert result.selected_count == 1
    assert result.rejected_count == 1
    assert result.selected_scenes == (matching_candidate,)
    assert result.has_selected_scenes is True


def test_prepare_scenes_returns_empty_selection() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    candidate = SceneCandidate(
        scene_id="S2A_CLOUDY_SCENE",
        acquisition_date=date(2024, 6, 10),
        cloud_cover=35.0,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    result = prepare_scenes(
        request=request,
        candidates=[candidate],
    )

    assert result.candidate_count == 1
    assert result.selected_count == 0
    assert result.rejected_count == 1
    assert result.selected_scenes == ()
    assert result.has_selected_scenes is False


def test_prepare_scenes_rejects_invalid_request() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 12, 31),
        end_date=date(2024, 1, 1),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=120.0,
    )

    with pytest.raises(ValueError) as error:
        prepare_scenes(
            request=request,
            candidates=[],
        )

    assert (
        "start_date must be earlier than or equal to end_date"
        in str(error.value)
    )
    assert (
        "max_cloud_cover must be between 0 and 100"
        in str(error.value)
    )