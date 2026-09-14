"Deterministic supervised candidate-tile selection"
from geoai_dataset_curation.sampling.contracts import (
    SamplingPolicy,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.eligibility import (
    assess_tile_sampling_eligibility,
)
from geoai_dataset_curation.sampling.policy import (
    LOOP1_SAMPLING_POLICY,
)
from geoai_dataset_curation.sampling.policy_validation import (
    validate_sampling_policy,
)
from geoai_dataset_curation.sampling.selection_validation import (
    validate_tile_sampling_selection,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


def select_tile_candidates(
    catalog: TileCatalog,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> TileSamplingSelection:
    "Select every explicitly supervised candidate in catalog order"
    catalog_errors = validate_tile_catalog(catalog)
    if catalog_errors:
        raise ValueError(
            "Cannot sample an invalid tile catalog: "
            + "; ".join(catalog_errors)
        )

    policy_errors = validate_sampling_policy(policy)
    if policy_errors:
        raise ValueError(
            "Cannot apply an invalid sampling policy: "
            + "; ".join(policy_errors)
        )

    assessments = tuple(
        (
            candidate,
            assess_tile_sampling_eligibility(candidate),
        )
        for candidate in catalog.tiles
    )

    selection = TileSamplingSelection(
        catalog_id=build_tile_catalog_id(catalog),
        selected_candidates=tuple(
            candidate
            for candidate, assessment in assessments
            if assessment.is_eligible
        ),
        excluded_tile_ids=tuple(
            candidate.tile_id
            for candidate, assessment in assessments
            if not assessment.is_eligible
        ),
    )

    selection_errors = validate_tile_sampling_selection(
        selection,
        catalog=catalog,
    )
    if selection_errors:
        raise ValueError(
            "Cannot produce an invalid sampling selection: "
            + "; ".join(selection_errors)
        )

    return selection