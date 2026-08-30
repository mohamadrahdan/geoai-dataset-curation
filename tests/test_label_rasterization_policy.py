from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.label_rasterization import (
    LOOP1_RASTERIZATION_POLICY,
    LabelRasterizationPolicy,
    OutOfGridRule,
    OverlapRule,
    PixelInclusionRule,
)


def test_loop1_policy_uses_pixel_center_rule() -> None:
    assert (
        LOOP1_RASTERIZATION_POLICY.pixel_inclusion
        == PixelInclusionRule.PIXEL_CENTER
    )


def test_loop1_policy_initializes_unlabeled_pixels_as_ignore() -> None:
    assert LOOP1_RASTERIZATION_POLICY.fill_value == LabelValue.IGNORE


def test_loop1_policy_rejects_conflicting_overlap() -> None:
    assert (
        LOOP1_RASTERIZATION_POLICY.overlap
        == OverlapRule.ERROR_ON_CONFLICT
    )


def test_loop1_policy_clips_partial_and_rejects_disjoint_geometry() -> None:
    assert (
        LOOP1_RASTERIZATION_POLICY.out_of_grid
        == OutOfGridRule.CLIP_PARTIAL_REJECT_DISJOINT
    )


def test_default_policy_matches_loop1_policy() -> None:
    assert LabelRasterizationPolicy() == LOOP1_RASTERIZATION_POLICY