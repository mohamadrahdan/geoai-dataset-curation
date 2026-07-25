"Serialization helpers for scene-preparation results"

from typing import Any
from geoai_dataset_curation.scene_preparation.contracts import (ScenePreparationResult)


def scene_preparation_result_to_dict(
    result: ScenePreparationResult,
) -> dict[str, Any]:
    "Convert a scene-preparation result into a serializable manifest"

    return {
        "source_id": result.source_id,
        "candidate_count": result.candidate_count,
        "selected_count": result.selected_count,
        "rejected_count": result.rejected_count,
        "has_selected_scenes": result.has_selected_scenes,
        "selected_scenes": [
            {
                "scene_id": scene.scene_id,
                "acquisition_date": scene.acquisition_date.isoformat(),
                "cloud_cover": scene.cloud_cover,
                "collection": scene.collection,
                "available_bands": list(scene.available_bands),
            }
            for scene in result.selected_scenes
        ],
    }