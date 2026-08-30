"Validation rules for label-rasterization requests"
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.validation import (
    validate_exact_raster_grid_spec,
)
from geoai_dataset_curation.label_rasterization.contracts import (
    LabelRasterizationRequest,
    LabelVectorSource,
)


REFERENCE_SUPERVISION_KINDS = {
    SupervisionKind.POSITIVE_REFERENCE,
    SupervisionKind.NEGATIVE_REFERENCE,
    SupervisionKind.HARD_NEGATIVE_REFERENCE,
}


def validate_label_vector_source(
    source: LabelVectorSource,
) -> tuple[str, ...]:
    "Validate one explicit vector-supervision source"

    errors: list[str] = []

    if not source.source_id.strip():
        errors.append("source_id must not be empty.")

    if not source.geometries:
        errors.append("geometries must contain at least one geometry.")

    if source.supervision not in REFERENCE_SUPERVISION_KINDS:
        errors.append(
            "supervision must represent explicit reference evidence."
        )
    return tuple(errors)


def validate_label_rasterization_request(
    request: LabelRasterizationRequest,
) -> tuple[str, ...]:
    "Validate one vector-to-label-raster request"
    errors: list[str] = []

    if not request.sources:
        errors.append("sources must contain at least one vector source.")

    if not request.output_name.strip():
        errors.append("output_name must not be empty.")

    source_ids = [
        source.source_id
        for source in request.sources
    ]

    if len(source_ids) != len(set(source_ids)):
        errors.append("source_id values must be unique.")

    for source in request.sources:
        errors.extend(
            f"{source.source_id or '<empty>'}: {error}"
            for error in validate_label_vector_source(source)
        )

    errors.extend(
        f"grid.{error}"
        for error in validate_exact_raster_grid_spec(request.grid)
    )
    return tuple(errors)