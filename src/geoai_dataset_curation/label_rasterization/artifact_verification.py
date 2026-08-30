"Verification of physical label rasters against artifact contracts"
from dataclasses import dataclass
from collections.abc import Iterable
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from geoai_dataset_curation.image_construction.raster_grid_verification import (
    RasterGridVerificationResult,
    verify_raster_against_grid,
)
from geoai_dataset_curation.label_rasterization.artifact_contract import (
    LabelRasterArtifactSpec,
)
from geoai_dataset_curation.label_rasterization.artifact_validation import (
    validate_label_raster_artifact_spec,
)


@dataclass(frozen=True)
class LabelRasterVerificationResult:
    "Result of checking one physical label raster against its contract"
    grid: RasterGridVerificationResult
    band_count_matches: bool
    dtype_matches: bool
    values_valid: bool

    @property
    def matches(self) -> bool:
        "Return whether all label-artifact checks passed"
        return (
            self.grid.matches
            and self.band_count_matches
            and self.dtype_matches
            and self.values_valid
        )


def verify_label_raster_artifact(
    *,
    metadata: RasterArtifactMetadata,
    observed_values: Iterable[int],
    spec: LabelRasterArtifactSpec,
) -> LabelRasterVerificationResult:
    "Verify raster metadata and observed pixel values against a label contract"
    errors = validate_label_raster_artifact_spec(spec)
    if errors:
        raise ValueError(
            "Invalid label-raster artifact spec: "
            + "; ".join(errors)
        )
    observed = {
        int(value)
        for value in observed_values
    }
    allowed = set(spec.allowed_values)
    return LabelRasterVerificationResult(
        grid=verify_raster_against_grid(
            metadata,
            spec.grid,
        ),
        band_count_matches=(
            metadata.band_count == spec.band_count
        ),
        dtype_matches=(
            metadata.dtypes == (spec.dtype,)
        ),
        values_valid=observed.issubset(allowed),
    )