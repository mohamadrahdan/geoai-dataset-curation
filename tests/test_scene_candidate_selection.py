from datetime import date
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    SceneSelectionRequest,
    select_scene_candidates,
)


def test_select_scene_candidates_keeps_matching_candidate() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    candidate = SceneCandidate(
        scene_id="S2A_MATCHING_SCENE",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8", "B11"),
    )

    selected = select_scene_candidates(
        request=request,
        candidates=[candidate],
    )

    assert selected == (candidate,)


def test_select_scene_candidates_rejects_candidate_outside_date_range() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    candidate = SceneCandidate(
        scene_id="S2A_OLD_SCENE",
        acquisition_date=date(2023, 12, 31),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    selected = select_scene_candidates(
        request=request,
        candidates=[candidate],
    )

    assert selected == ()


def test_select_scene_candidates_rejects_excessive_cloud_cover() -> None:
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
        acquisition_date=date(2024, 5, 18),
        cloud_cover=35.0,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    selected = select_scene_candidates(
        request=request,
        candidates=[candidate],
    )

    assert selected == ()


def test_select_scene_candidates_rejects_wrong_collection() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    candidate = SceneCandidate(
        scene_id="S2A_WRONG_COLLECTION",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2",
        available_bands=("B2", "B3", "B4", "B8"),
    )

    selected = select_scene_candidates(
        request=request,
        candidates=[candidate],
    )

    assert selected == ()


def test_select_scene_candidates_rejects_missing_required_band() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    candidate = SceneCandidate(
        scene_id="S2A_MISSING_BAND",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4"),
    )

    selected = select_scene_candidates(
        request=request,
        candidates=[candidate],
    )

    assert selected == ()