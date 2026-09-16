"Stable identity helpers for deterministic tile selections"
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    TILE_SAMPLING_SELECTION_SCHEMA_VERSION,
    SamplingPolicy,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.policy import LOOP1_SAMPLING_POLICY
from geoai_dataset_curation.sampling.policy_validation import (
    validate_sampling_policy,
)
from geoai_dataset_curation.sampling.selection_validation import (
    validate_tile_sampling_selection,
)
from geoai_dataset_curation.tiling.catalog import TileCatalog
from geoai_dataset_curation.tiling.identity import _build_sha256_id


def sampling_policy_identity_payload(
    policy: SamplingPolicy,
) -> dict[str, Any]:
    "Return the canonical identity payload for one sampling policy"
    errors = validate_sampling_policy(policy)
    if errors:
        raise ValueError(
            "Cannot identify an invalid sampling policy: "
            + "; ".join(errors)
        )
    return {
        "select_all_eligible": policy.select_all_eligible,
        "exclude_all_ignore": policy.exclude_all_ignore,
        "order": policy.order.value,
        "hard_negative_handling": policy.hard_negative_handling.value,
    }


def tile_sampling_selection_identity_payload(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> dict[str, Any]:
    "Return the canonical identity payload for one tile selection"
    errors = validate_tile_sampling_selection(
        selection,
        catalog=catalog,
    )
    if errors:
        raise ValueError(
            "Cannot identify an invalid tile sampling selection: "
            + "; ".join(errors)
        )

    return {
        "schema_version": TILE_SAMPLING_SELECTION_SCHEMA_VERSION,
        "tile_catalog_id": selection.catalog_id,
        "policy": sampling_policy_identity_payload(policy),
        "selected_tile_ids": [
            candidate.tile_id
            for candidate in selection.selected_candidates
        ],
        "excluded_tile_ids": list(selection.excluded_tile_ids),
    }


def build_tile_sampling_selection_id(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> str:
    "Build a stable identifier for one deterministic tile selection"
    payload = tile_sampling_selection_identity_payload(
        selection,
        catalog=catalog,
        policy=policy,
    )
    return _build_sha256_id(payload)