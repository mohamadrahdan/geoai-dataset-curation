"Validation rules for Sentinel-2 scene-selection requests"

from geoai_dataset_curation.scene_preparation.contracts import (
    SceneSelectionRequest,
)


def validate_scene_selection_request(
    request: SceneSelectionRequest,
) -> tuple[str, ...]:
    "Return all detected validation errors for one selection request"

    errors: list[str] = []
    if request.start_date > request.end_date:
        errors.append(
            "start_date must be earlier than or equal to end_date"
        )

    if not request.source_id.strip():
        errors.append("source_id must not be empty")

    if not request.collection.strip():
        errors.append("collection must not be empty")

    if not request.required_bands:
        errors.append("required_bands must contain at least one band")

    if len(set(request.required_bands)) != len(request.required_bands):
        errors.append("required_bands must not contain duplicates")

    if not 0.0 <= request.max_cloud_cover <= 100.0:
        errors.append("max_cloud_cover must be between 0 and 100")

    return tuple(errors)