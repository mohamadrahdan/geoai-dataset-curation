from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.label_rasterization import (
    LOOP1_RASTERIZATION_POLICY,
    LabelRasterizationPolicy,
    validate_label_rasterization_policy,
)


def test_loop1_rasterization_policy_is_valid() -> None:
    assert (
        validate_label_rasterization_policy(
            LOOP1_RASTERIZATION_POLICY
        )
        == ()
    )


def test_negative_fill_value_is_rejected() -> None:
    policy = LabelRasterizationPolicy(
        fill_value=LabelValue.NEGATIVE
    )
    errors = validate_label_rasterization_policy(policy)
    assert (
        "fill_value must be IGNORE so unlabeled pixels do not "
        "become negative targets."
        in errors
    )


def test_positive_fill_value_is_rejected() -> None:
    policy = LabelRasterizationPolicy(
        fill_value=LabelValue.POSITIVE
    )
    errors = validate_label_rasterization_policy(policy)
    assert any(
        "fill_value must be IGNORE" in error
        for error in errors
    )