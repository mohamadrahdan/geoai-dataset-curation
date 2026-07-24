from datetime import date
from geoai_dataset_curation.scene_preparation import (
    SceneSelectionRequest,
    validate_scene_selection_request,
)


def test_validate_scene_selection_request_accepts_valid_request() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )

    errors = validate_scene_selection_request(request)

    assert errors == ()


def test_validate_scene_selection_request_reports_invalid_date_range() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 12, 31),
        end_date=date(2024, 1, 1),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )

    errors = validate_scene_selection_request(request)

    assert "start_date must be earlier than or equal to end_date" in errors


def test_validate_scene_selection_request_reports_empty_fields() -> None:
    request = SceneSelectionRequest(
        source_id="   ",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="",
        required_bands=(),
        max_cloud_cover=20.0,
    )

    errors = validate_scene_selection_request(request)

    assert "source_id must not be empty" in errors
    assert "collection must not be empty" in errors
    assert "required_bands must contain at least one band" in errors


def test_validate_scene_selection_request_reports_duplicate_bands() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B4"),
        max_cloud_cover=20.0,
    )

    errors = validate_scene_selection_request(request)

    assert "required_bands must not contain duplicates" in errors


def test_validate_scene_selection_request_reports_invalid_cloud_cover() -> None:
    request = SceneSelectionRequest(
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=120.0,
    )

    errors = validate_scene_selection_request(request)

    assert "max_cloud_cover must be between 0 and 100" in errors