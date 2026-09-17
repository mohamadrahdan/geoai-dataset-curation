"Validation of candidate-tile sampling contracts"
from geoai_dataset_curation.sampling.contracts import (
    SamplingEligibilityReason,
    SamplingEligibilityStatus,
    TileSamplingEligibility,
)
from geoai_dataset_curation.tiling.catalog import TileLabelClass


def _is_sha256_id(value: str) -> bool:
    "Return whether a value is a canonical SHA-256 identity"
    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(
            character in "0123456789abcdef"
            for character in digest
        )
    )


def validate_tile_sampling_eligibility(
    assessment: TileSamplingEligibility,
) -> tuple[str, ...]:
    "Return consistency errors for one sampling assessment"
    errors: list[str] = []
    if not _is_sha256_id(assessment.tile_id):
        errors.append("tile_id must be a valid SHA-256 identity.")
    if not isinstance(
        assessment.label_class,
        TileLabelClass,
    ):
        errors.append("label_class must be a TileLabelClass.")
    if not isinstance(
        assessment.status,
        SamplingEligibilityStatus,
    ):
        errors.append("status must be a SamplingEligibilityStatus.")
    if not isinstance(
        assessment.reason,
        SamplingEligibilityReason,
    ):
        errors.append("reason must be a SamplingEligibilityReason.")

    enum_fields_are_valid = (
        isinstance(
            assessment.label_class,
            TileLabelClass,
        )
        and isinstance(
            assessment.status,
            SamplingEligibilityStatus,
        )
        and isinstance(
            assessment.reason,
            SamplingEligibilityReason,
        )
    )

    if not enum_fields_are_valid:
        return tuple(errors)
    if assessment.label_class == TileLabelClass.ALL_IGNORE:
        expected_status = (
            SamplingEligibilityStatus.INELIGIBLE
        )
        expected_reason = (
            SamplingEligibilityReason.ALL_PIXELS_IGNORED
        )
    else:
        expected_status = (
            SamplingEligibilityStatus.ELIGIBLE
        )
        expected_reason = (
            SamplingEligibilityReason
            .SUPERVISED_PIXELS_PRESENT
        )
    if assessment.status != expected_status:
        errors.append("status must match the candidate label_class.")
    if assessment.reason != expected_reason:
        errors.append("reason must match the candidate label_class.")
    return tuple(errors)