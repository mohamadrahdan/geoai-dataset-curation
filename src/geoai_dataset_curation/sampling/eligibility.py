"Eligibility assessment for candidate-tile sampling"
from geoai_dataset_curation.sampling.contracts import (
    SamplingEligibilityReason,
    SamplingEligibilityStatus,
    TileSamplingEligibility,
)
from geoai_dataset_curation.sampling.validation import (
    validate_tile_sampling_eligibility,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileLabelClass,
    validate_tile_candidate_record,
)


def assess_tile_sampling_eligibility(
    candidate: TileCandidateRecord,
) -> TileSamplingEligibility:
    "Assess whether one valid tile may enter supervised sampling"
    candidate_errors = validate_tile_candidate_record(
        candidate
    )
    if candidate_errors:
        raise ValueError(
            "Cannot assess invalid tile candidate: "
            + "; ".join(candidate_errors)
        )

    if candidate.label_class == TileLabelClass.ALL_IGNORE:
        assessment = TileSamplingEligibility(
            tile_id=candidate.tile_id,
            label_class=candidate.label_class,
            status=SamplingEligibilityStatus.INELIGIBLE,
            reason=(
                SamplingEligibilityReason
                .ALL_PIXELS_IGNORED
            ),
        )
    else:
        assessment = TileSamplingEligibility(
            tile_id=candidate.tile_id,
            label_class=candidate.label_class,
            status=SamplingEligibilityStatus.ELIGIBLE,
            reason=(
                SamplingEligibilityReason
                .SUPERVISED_PIXELS_PRESENT
            ),
        )
    assessment_errors = (
        validate_tile_sampling_eligibility(
            assessment
        )
    )
    if assessment_errors:
        raise ValueError(
            "Cannot produce invalid sampling assessment: "
            + "; ".join(assessment_errors)
        )
    return assessment