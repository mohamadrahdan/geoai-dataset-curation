"Validation of leakage-aware spatial split contracts"
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split.contracts import (
    SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION,
    SpatialSplitAssignment,
    SpatialSplitCatalog,
    SpatialSplitName,
)


def _is_sha256_id(value: object) -> bool:
    "Return whether a value is a canonical SHA-256 identity"
    if not isinstance(value, str):
        return False

    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(
            character in "0123456789abcdef"
            for character in digest
        )
    )


def validate_spatial_split_assignment(
    assignment: SpatialSplitAssignment,
) -> tuple[str, ...]:
    "Return contract errors for one spatial split assignment"
    errors: list[str] = []

    if not _is_sha256_id(assignment.pair_id):
        errors.append(
            "pair_id must be a valid SHA-256 identity."
        )

    if not _is_sha256_id(assignment.tile_id):
        errors.append(
            "tile_id must be a valid SHA-256 identity."
        )

    if not _is_sha256_id(
        assignment.spatial_group_id
    ):
        errors.append(
            "spatial_group_id must be a valid "
            "SHA-256 identity."
        )

    if not isinstance(
        assignment.split,
        SpatialSplitName,
    ):
        errors.append(
            "split must be a SpatialSplitName."
        )

    return tuple(errors)


def validate_spatial_split_catalog(
    catalog: SpatialSplitCatalog,
    *,
    pair_catalog: ImageMaskPairCatalog,
) -> tuple[str, ...]:
    "Return consistency errors for one spatial split catalog"
    errors: list[str] = []

    if (
        catalog.schema_version
        != SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION
    ):
        errors.append(
            "schema_version is not supported."
        )

    if (
        not isinstance(catalog.output_name, str)
        or not catalog.output_name.strip()
    ):
        errors.append(
            "output_name must not be empty."
        )

    expected_pair_catalog_id = (
        build_image_mask_pair_catalog_id(
            pair_catalog
        )
    )
    if (
        catalog.pair_catalog_id
        != expected_pair_catalog_id
    ):
        errors.append(
            "pair_catalog_id must match "
            "the pair catalog."
        )

    identity_fields = (
        (
            "pair_qc_report_id",
            catalog.pair_qc_report_id,
        ),
        (
            "visual_review_catalog_id",
            catalog.visual_review_catalog_id,
        ),
        (
            "grouping_policy_id",
            catalog.grouping_policy_id,
        ),
        (
            "assignment_policy_id",
            catalog.assignment_policy_id,
        ),
    )

    for field_name, value in identity_fields:
        if not _is_sha256_id(value):
            errors.append(
                f"{field_name} must be a valid "
                "SHA-256 identity."
            )

    if not isinstance(catalog.assignments, tuple):
        errors.append(
            "assignments must be a tuple."
        )
        return tuple(errors)

    if not catalog.assignments:
        errors.append(
            "assignments must not be empty."
        )

    valid_assignments: list[
        SpatialSplitAssignment
    ] = []

    for index, assignment in enumerate(
        catalog.assignments
    ):
        if not isinstance(
            assignment,
            SpatialSplitAssignment,
        ):
            errors.append(
                f"assignments[{index}] must be a "
                "SpatialSplitAssignment."
            )
            continue

        valid_assignments.append(assignment)

        assignment_errors = (
            validate_spatial_split_assignment(
                assignment
            )
        )
        errors.extend(
            f"assignments[{index}].{error}"
            for error in assignment_errors
        )

    observed_pair_ids = tuple(
        assignment.pair_id
        for assignment in valid_assignments
    )
    observed_tile_ids = tuple(
        assignment.tile_id
        for assignment in valid_assignments
    )
    expected_pair_ids = tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )

    if (
        len(set(observed_pair_ids))
        != len(observed_pair_ids)
    ):
        errors.append(
            "assignment pair_id values "
            "must be unique."
        )

    if (
        len(set(observed_tile_ids))
        != len(observed_tile_ids)
    ):
        errors.append(
            "assignment tile_id values "
            "must be unique."
        )

    if observed_pair_ids != expected_pair_ids:
        errors.append(
            "assignments must cover every pair "
            "in catalog order."
        )

    pairs_by_id = {
        pair.pair_id: pair
        for pair in pair_catalog.pairs
    }

    for index, assignment in enumerate(
        valid_assignments
    ):
        pair = pairs_by_id.get(
            assignment.pair_id
        )
        if (
            pair is not None
            and assignment.tile_id != pair.tile_id
        ):
            errors.append(
                f"assignments[{index}].tile_id "
                "must match the assigned pair."
            )

    split_by_group_id: dict[
        str,
        SpatialSplitName,
    ] = {}
    conflicting_group_ids: set[str] = set()

    for assignment in valid_assignments:
        previous_split = (
            split_by_group_id.setdefault(
                assignment.spatial_group_id,
                assignment.split,
            )
        )
        if previous_split != assignment.split:
            conflicting_group_ids.add(
                assignment.spatial_group_id
            )

    if conflicting_group_ids:
        errors.append(
            "each spatial_group_id must belong "
            "to exactly one split."
        )

    return tuple(errors)