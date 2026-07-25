"End-to-end Sentinel-2 scene preparation pipeline"

from collections.abc import Iterable
from geoai_dataset_curation.scene_preparation.selection import (select_scene_candidates)
from geoai_dataset_curation.scene_preparation.validation import (validate_scene_selection_request)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneCandidate,
    ScenePreparationResult,
    SceneSelectionRequest,
)


def prepare_scenes(
    request: SceneSelectionRequest,
    candidates: Iterable[SceneCandidate],
) -> ScenePreparationResult:
    "Validate a request and prepare matching scene candidates"

    errors = validate_scene_selection_request(request)
    if errors:
        raise ValueError("; ".join(errors))

    candidate_list = tuple(candidates)
    selected_scenes = select_scene_candidates(
        request=request,
        candidates=candidate_list,
    )

    return ScenePreparationResult(
        source_id=request.source_id,
        candidate_count=len(candidate_list),
        selected_count=len(selected_scenes),
        rejected_count=len(candidate_list) - len(selected_scenes),
        selected_scenes=selected_scenes,
    )