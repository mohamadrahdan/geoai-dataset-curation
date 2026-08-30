"Validation rules for expected label-raster artifacts"
from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.image_construction.validation import (
    validate_exact_raster_grid_spec,
)
from geoai_dataset_curation.label_rasterization.artifact_contract import (
    LOOP1_LABEL_ALLOWED_VALUES,
    LabelRasterArtifactSpec,
)


def validate_label_raster_artifact_spec(
    spec: LabelRasterArtifactSpec,
) -> tuple[str, ...]:
    "Validate one expected Loop 1 label-raster artifact"
    errors: list[str] = []
    if not spec.output_name.strip():
        errors.append("output_name must not be empty.")
    if spec.band_count != 1:
        errors.append("band_count must be exactly 1.")
    if spec.dtype != "uint8":
        errors.append("dtype must be uint8.")
    if set(spec.allowed_values) != set(LOOP1_LABEL_ALLOWED_VALUES):
        errors.append("allowed_values must match the Loop 1 label values.")
    if int(LabelValue.IGNORE) not in spec.allowed_values:
        errors.append(
            "allowed_values must include the IGNORE value."
        )

    errors.extend(
        f"grid.{error}"
        for error in validate_exact_raster_grid_spec(spec.grid)
    )
    return tuple(errors)