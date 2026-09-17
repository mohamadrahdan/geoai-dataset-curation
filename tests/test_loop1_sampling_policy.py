from dataclasses import replace
from geoai_dataset_curation.sampling import (
    HardNegativeHandling,
    LOOP1_SAMPLING_POLICY,
    SamplingOrder,
    validate_sampling_policy,
)


def test_loop1_sampling_policy_has_selected_parameters() -> None:
    assert LOOP1_SAMPLING_POLICY.select_all_eligible is True
    assert LOOP1_SAMPLING_POLICY.exclude_all_ignore is True
    assert (
        LOOP1_SAMPLING_POLICY.order
        == SamplingOrder.CATALOG_ORDER
    )
    assert (
        LOOP1_SAMPLING_POLICY.hard_negative_handling
        == HardNegativeHandling.REQUIRE_SOURCE_PROVENANCE
    )


def test_loop1_sampling_policy_is_valid() -> None:
    assert validate_sampling_policy(
        LOOP1_SAMPLING_POLICY
    ) == ()


def test_policy_validation_rejects_all_ignore_inclusion() -> None:
    policy = replace(
        LOOP1_SAMPLING_POLICY,
        exclude_all_ignore=False,
    )
    errors = validate_sampling_policy(policy)
    assert (
        "exclude_all_ignore must be true for "
        "supervised sampling."
        in errors
    )


def test_policy_validation_rejects_discarding_eligible_tiles() -> None:
    policy = replace(
        LOOP1_SAMPLING_POLICY,
        select_all_eligible=False,
    )
    errors = validate_sampling_policy(policy)
    assert (
        "select_all_eligible must be true for "
        "the Loop 1 baseline."
        in errors
    )


def test_policy_validation_rejects_non_enum_fields() -> None:
    policy = replace(
        LOOP1_SAMPLING_POLICY,
        order="catalog_order",  # type: ignore[arg-type]
        hard_negative_handling=(  # type: ignore[arg-type]
            "require_source_provenance"
        ),
    )
    errors = validate_sampling_policy(policy)
    assert "order must be a SamplingOrder." in errors
    assert (
        "hard_negative_handling must be "
        "a HardNegativeHandling."
        in errors
    )