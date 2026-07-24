"Selection of Sentinel-2 scene candidates"

from collections.abc import Iterable
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneCandidate,
    SceneSelectionRequest,
)


def select_scene_candidates(
    request: SceneSelectionRequest,
    candidates: Iterable[SceneCandidate],
) -> tuple[SceneCandidate, ...]:
    "Return scene candidates that satisfy all selection criteria"

    required_bands = set(request.required_bands)
    return tuple(
        candidate
        for candidate in candidates
        if request.start_date
        <= candidate.acquisition_date
        <= request.end_date
        and candidate.collection == request.collection
        and candidate.cloud_cover <= request.max_cloud_cover
        and required_bands.issubset(candidate.available_bands)
    )