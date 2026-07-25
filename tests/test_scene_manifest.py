from datetime import date
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    ScenePreparationResult,
    scene_preparation_result_to_dict,
)


def test_scene_preparation_result_to_dict_serializes_selected_scenes() -> None:
    candidate = SceneCandidate(
        scene_id="S2A_SELECTED_SCENE",
        acquisition_date=date(2024, 5, 18),
        cloud_cover=8.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=("B2", "B3", "B4", "B8"),
    )
    result = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=2,
        selected_count=1,
        rejected_count=1,
        selected_scenes=(candidate,),
    )

    manifest = scene_preparation_result_to_dict(result)
    assert manifest == {
        "source_id": "padena_aoi",
        "candidate_count": 2,
        "selected_count": 1,
        "rejected_count": 1,
        "has_selected_scenes": True,
        "selected_scenes": [
            {
                "scene_id": "S2A_SELECTED_SCENE",
                "acquisition_date": "2024-05-18",
                "cloud_cover": 8.5,
                "collection": "COPERNICUS/S2_SR_HARMONIZED",
                "available_bands": ["B2", "B3", "B4", "B8"],
            }
        ],
    }


def test_scene_preparation_result_to_dict_serializes_empty_selection() -> None:
    result = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=1,
        selected_count=0,
        rejected_count=1,
        selected_scenes=(),
    )

    manifest = scene_preparation_result_to_dict(result)
    assert manifest["has_selected_scenes"] is False
    assert manifest["selected_scenes"] == []