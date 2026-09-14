"Validation of supervised candidate-tile sampling policies"
from geoai_dataset_curation.sampling.contracts import (
    HardNegativeHandling,
    SamplingOrder,
    SamplingPolicy,
)


def validate_sampling_policy(
    policy: SamplingPolicy,
) -> tuple[str, ...]:
    "Return consistency errors for one sampling policy"
    errors: list[str] = []
    if not isinstance(policy.select_all_eligible, bool):
        errors.append("select_all_eligible must be a bool.")
    elif not policy.select_all_eligible:
        errors.append(
            "select_all_eligible must be true for "
            "the Loop 1 baseline."
        )

    if not isinstance(policy.exclude_all_ignore, bool):
        errors.append("exclude_all_ignore must be a bool.")
    elif not policy.exclude_all_ignore:
        errors.append(
            "exclude_all_ignore must be true for "
            "supervised sampling."
        )

    if not isinstance(policy.order, SamplingOrder):
        errors.append("order must be a SamplingOrder.")
    elif policy.order != SamplingOrder.CATALOG_ORDER:
        errors.append("order must preserve deterministic catalog order.")

    if not isinstance(
        policy.hard_negative_handling,
        HardNegativeHandling,
    ):
        errors.append(
            "hard_negative_handling must be "
            "a HardNegativeHandling."
        )
    elif (
        policy.hard_negative_handling
        != HardNegativeHandling.REQUIRE_SOURCE_PROVENANCE
    ):
        errors.append(
            "hard-negative source provenance "
            "must be required."
        )
    return tuple(errors)