"Validation of deterministic candidate-tile sampling selections"
from geoai_dataset_curation.sampling.contracts import (
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.eligibility import (
    assess_tile_sampling_eligibility,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


def validate_tile_sampling_selection(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
) -> tuple[str, ...]:
    "Return consistency errors for one sampling selection"
    catalog_errors = validate_tile_catalog(catalog)
    if catalog_errors:
        return tuple(
            f"catalog.{error}"
            for error in catalog_errors
        )

    errors: list[str] = []

    if selection.catalog_id != build_tile_catalog_id(catalog):
        errors.append("catalog_id must match the candidate catalog.")

    catalog_by_id = {
        candidate.tile_id: candidate
        for candidate in catalog.tiles
    }
    selected_ids = tuple(
        candidate.tile_id
        for candidate in selection.selected_candidates
    )
    excluded_ids = selection.excluded_tile_ids

    if len(set(selected_ids)) != len(selected_ids):
        errors.append("selected candidate IDs must be unique.")
    if len(set(excluded_ids)) != len(excluded_ids):
        errors.append("excluded tile IDs must be unique.")
    if set(selected_ids) & set(excluded_ids):
        errors.append("selected and excluded tile IDs must not overlap.")
    if (
        set(selected_ids) | set(excluded_ids)
        != set(catalog_by_id)
    ):
        errors.append(
            "selected and excluded tile IDs must "
            "partition the catalog."
        )
    assessments = tuple(
        (
            candidate,
            assess_tile_sampling_eligibility(candidate),
        )
        for candidate in catalog.tiles
    )
    expected_selected = tuple(
        candidate
        for candidate, assessment in assessments
        if assessment.is_eligible
    )
    expected_excluded_ids = tuple(
        candidate.tile_id
        for candidate, assessment in assessments
        if not assessment.is_eligible
    )
    if selection.selected_candidates != expected_selected:
        errors.append(
            "selected_candidates must contain every supervised "
            "tile in catalog order."
        )
    if selection.excluded_tile_ids != expected_excluded_ids:
        errors.append(
            "excluded_tile_ids must contain only all-ignore "
            "tiles in catalog order."
        )
    for candidate in selection.selected_candidates:
        catalog_candidate = catalog_by_id.get(
            candidate.tile_id
        )
        if (
            catalog_candidate is not None
            and candidate != catalog_candidate
        ):
            errors.append(
                "selected candidate content must match "
                "the catalog."
            )
            break
    return tuple(errors)