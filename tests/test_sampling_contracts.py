from geoai_dataset_curation.sampling import (
    SamplingEligibilityReason,
    SamplingEligibilityStatus,
    TileSamplingEligibility,
)
from geoai_dataset_curation.tiling import TileLabelClass


TILE_ID = "sha256:" + ("a" * 64)


def test_sampling_eligibility_preserves_contract_fields() -> None:
    assessment = TileSamplingEligibility(
        tile_id=TILE_ID,
        label_class=TileLabelClass.POSITIVE,
        status=SamplingEligibilityStatus.ELIGIBLE,
        reason=(
            SamplingEligibilityReason
            .SUPERVISED_PIXELS_PRESENT
        ),
    )
    assert assessment.tile_id == TILE_ID
    assert assessment.label_class == TileLabelClass.POSITIVE
    assert (
        assessment.status
        == SamplingEligibilityStatus.ELIGIBLE
    )
    assert (
        assessment.reason
        == SamplingEligibilityReason
        .SUPERVISED_PIXELS_PRESENT
    )
    assert assessment.is_eligible is True


def test_ineligible_assessment_reports_false() -> None:
    assessment = TileSamplingEligibility(
        tile_id=TILE_ID,
        label_class=TileLabelClass.ALL_IGNORE,
        status=SamplingEligibilityStatus.INELIGIBLE,
        reason=(
            SamplingEligibilityReason
            .ALL_PIXELS_IGNORED
        ),
    )
    assert assessment.is_eligible is False