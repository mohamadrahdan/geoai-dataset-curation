"Validation rules for region-independent study areas"
from geoai_dataset_curation.scene_preparation.contracts import (
    StudyAreaSpec,
)


def validate_study_area(
    study_area: StudyAreaSpec,
) -> tuple[str, ...]:
    "Return all detected validation errors for one study area"
    errors: list[str] = []
    if not study_area.study_area_id.strip():
        errors.append("study_area_id must not be empty")

    if not study_area.source_id.strip():
        errors.append("source_id must not be empty")

    if not study_area.crs.strip():
        errors.append("crs must not be empty")

    geometry = study_area.geometry

    if geometry.is_empty:
        errors.append("geometry must not be empty")

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        errors.append(
            "geometry must be a Polygon or MultiPolygon"
        )

    if not geometry.is_valid:
        errors.append("geometry must be valid")
    return tuple(errors)