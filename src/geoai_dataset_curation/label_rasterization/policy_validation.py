"Validation rules for label-rasterization policies"
from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.label_rasterization.policy import (
    LabelRasterizationPolicy,
    OutOfGridRule,
    OverlapRule,
    PixelInclusionRule,
)


def validate_label_rasterization_policy(
    policy: LabelRasterizationPolicy,
) -> tuple[str, ...]:
    "Validate one Loop 1 label-rasterization policy"
    errors: list[str] = []

    if policy.pixel_inclusion != PixelInclusionRule.PIXEL_CENTER:
        errors.append("pixel_inclusion must use the pixel-center rule.")

    if policy.overlap != OverlapRule.ERROR_ON_CONFLICT:
        errors.append("overlap must reject conflicting supervision.")

    if (
        policy.out_of_grid
        != OutOfGridRule.CLIP_PARTIAL_REJECT_DISJOINT
    ):
        errors.append(
            "out_of_grid must clip partial geometries and reject "
            "fully disjoint geometries."
        )

    if policy.fill_value != LabelValue.IGNORE:
        errors.append(
            "fill_value must be IGNORE so unlabeled pixels do not "
            "become negative targets."
        )

    return tuple(errors)