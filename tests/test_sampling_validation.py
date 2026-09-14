from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    SamplingEligibilityReason,
    SamplingEligibilityStatus,
    TileSamplingEligibility,
    assess_tile_sampling_eligibility,
    validate_tile_sampling_eligibility,
)
from geoai_dataset_curation.tiling import (
    TileCandidateRecord,
    TileLabelClass,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
TILE_ID = "sha256:" + ("c" * 64)


def make_candidate(
    *,
    positive_pixel_count: int = 1,
    negative_pixel_count: int = 0,
    ignore_pixel_count: int = 15,
) -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id=TILE_ID,
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=100.0,
        bottom=160.0,
        right=140.0,
        top=200.0,
        positive_pixel_count=positive_pixel_count,
        negative_pixel_count=negative_pixel_count,
        ignore_pixel_count=ignore_pixel_count,
    )


@pytest.mark.parametrize(
    "candidate",
    [
        make_candidate(),
        make_candidate(
            positive_pixel_count=0,
            negative_pixel_count=1,
        ),
    ],
)
def test_supervised_candidate_is_eligible(
    candidate: TileCandidateRecord,
) -> None:
    assessment = assess_tile_sampling_eligibility(candidate)
    assert assessment.is_eligible is True
    assert (
        assessment.status
        == SamplingEligibilityStatus.ELIGIBLE
    )
    assert (
        assessment.reason
        == SamplingEligibilityReason
        .SUPERVISED_PIXELS_PRESENT
    )
    assert validate_tile_sampling_eligibility(assessment) == ()


def test_all_ignore_candidate_is_ineligible() -> None:
    candidate = make_candidate(
        positive_pixel_count=0,
        negative_pixel_count=0,
        ignore_pixel_count=16,
    )

    assessment = assess_tile_sampling_eligibility(candidate)

    assert assessment.label_class == TileLabelClass.ALL_IGNORE
    assert assessment.is_eligible is False
    assert (
        assessment.status
        == SamplingEligibilityStatus.INELIGIBLE
    )
    assert (
        assessment.reason
        == SamplingEligibilityReason
        .ALL_PIXELS_IGNORED
    )
    assert validate_tile_sampling_eligibility(
        assessment
    ) == ()


def test_assessment_preserves_candidate_identity() -> None:
    candidate = make_candidate()
    assessment = assess_tile_sampling_eligibility(candidate)
    assert assessment.tile_id == candidate.tile_id
    assert assessment.label_class == candidate.label_class


def test_assessment_rejects_invalid_candidate() -> None:
    candidate = make_candidate(
        ignore_pixel_count=14,
    )

    with pytest.raises(
        ValueError,
        match="Cannot assess invalid tile candidate",
    ):
        assess_tile_sampling_eligibility(candidate)


def test_validation_rejects_invalid_identity() -> None:
    assessment = TileSamplingEligibility(
        tile_id="not-a-sha256-id",
        label_class=TileLabelClass.POSITIVE,
        status=SamplingEligibilityStatus.ELIGIBLE,
        reason=(
            SamplingEligibilityReason
            .SUPERVISED_PIXELS_PRESENT
        ),
    )
    errors = validate_tile_sampling_eligibility(assessment)
    assert (
        "tile_id must be a valid SHA-256 identity."
        in errors
    )


def test_validation_rejects_inconsistent_status_and_reason() -> None:
    valid = assess_tile_sampling_eligibility(
        make_candidate()
    )
    inconsistent = replace(
        valid,
        status=SamplingEligibilityStatus.INELIGIBLE,
        reason=(
            SamplingEligibilityReason
            .ALL_PIXELS_IGNORED
        ),
    )

    errors = validate_tile_sampling_eligibility(
        inconsistent
    )
    assert (
        "status must match the candidate label_class."
        in errors
    )
    assert (
        "reason must match the candidate label_class."
        in errors
    )


def test_validation_rejects_non_enum_fields() -> None:
    assessment = TileSamplingEligibility(
        tile_id=TILE_ID,
        label_class="positive",  # type: ignore[arg-type]
        status="eligible",  # type: ignore[arg-type]
        reason=(  # type: ignore[arg-type]
            "supervised_pixels_present"
        ),
    )

    errors = validate_tile_sampling_eligibility(assessment)
    assert (
        "label_class must be a TileLabelClass."
        in errors
    )
    assert (
        "status must be a SamplingEligibilityStatus."
        in errors
    )
    assert (
        "reason must be a SamplingEligibilityReason."
        in errors
    )