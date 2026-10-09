"Validation for relationship and leakage-group catalogs."
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
)
from geoai_dataset_curation.spatial_split.relationship_identity import (
    build_spatial_grouping_policy_id,
    build_spatial_leakage_group_id,
    build_spatial_relationship_catalog_id,
)
from geoai_dataset_curation.spatial_split.relationship_validation import (
    _is_sha256_id,
    validate_spatial_grouping_policy,
    validate_spatial_leakage_group,
    validate_spatial_pair_relationship,
    validate_spatial_tile_footprint,
)


def _axis_overlap_and_gap(
    first_start: int,
    first_stop: int,
    second_start: int,
    second_stop: int,
) -> tuple[int, int]:
    overlap = max(0, min(first_stop, second_stop) - max(first_start, second_start))
    if overlap > 0:
        return overlap, 0

    gap = max(first_start - second_stop, second_start - first_stop, 0)
    return 0, gap


def _expected_geometry(
    first: SpatialTileFootprint,
    second: SpatialTileFootprint,
    policy: SpatialGroupingPolicy,
) -> tuple[int, int, int, int, bool]:
    row_overlap, row_gap = _axis_overlap_and_gap(
        first.row_offset_pixels,
        first.row_stop_pixels,
        second.row_offset_pixels,
        second.row_stop_pixels,
    )
    column_overlap, column_gap = _axis_overlap_and_gap(
        first.column_offset_pixels,
        first.column_stop_pixels,
        second.column_offset_pixels,
        second.column_stop_pixels,
    )
    linked = row_gap**2 + column_gap**2 <= policy.maximum_gap_pixels**2
    return row_overlap, column_overlap, row_gap, column_gap, linked


def validate_spatial_relationship_catalog(
    catalog: SpatialRelationshipCatalog,
    *,
    policy: SpatialGroupingPolicy,
) -> tuple[str, ...]:
    errors: list[str] = []

    if catalog.schema_version != SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION:
        errors.append("schema_version is not supported.")

    if not isinstance(catalog.output_name, str) or not catalog.output_name.strip():
        errors.append("output_name must not be empty.")

    for field_name, value in (
        ("pair_catalog_id", catalog.pair_catalog_id),
        ("tile_catalog_id", catalog.tile_catalog_id),
        ("grouping_policy_id", catalog.grouping_policy_id),
    ):
        if not _is_sha256_id(value):
            errors.append(f"{field_name} must be a valid SHA-256 identity.")

    policy_errors = validate_spatial_grouping_policy(policy)
    errors.extend(f"policy.{error}" for error in policy_errors)

    if not policy_errors:
        expected_policy_id = build_spatial_grouping_policy_id(policy)
        if catalog.grouping_policy_id != expected_policy_id:
            errors.append("grouping_policy_id must match the grouping policy.")

    if not isinstance(catalog.footprints, tuple):
        errors.append("footprints must be a tuple.")
        return tuple(errors)

    if not catalog.footprints:
        errors.append("footprints must not be empty.")
        return tuple(errors)

    valid_footprints: list[SpatialTileFootprint] = []
    for index, footprint in enumerate(catalog.footprints):
        if not isinstance(footprint, SpatialTileFootprint):
            errors.append(f"footprints[{index}] must be a SpatialTileFootprint.")
            continue

        valid_footprints.append(footprint)
        footprint_errors = validate_spatial_tile_footprint(footprint)
        errors.extend(
            f"footprints[{index}].{error}"
            for error in footprint_errors
        )

    pair_ids = tuple(footprint.pair_id for footprint in valid_footprints)
    tile_ids = tuple(footprint.tile_id for footprint in valid_footprints)

    if len(set(pair_ids)) != len(pair_ids):
        errors.append("footprint pair_id values must be unique.")

    if len(set(tile_ids)) != len(tile_ids):
        errors.append("footprint tile_id values must be unique.")

    if not isinstance(catalog.relationships, tuple):
        errors.append("relationships must be a tuple.")
        return tuple(errors)

    expected_relationship_count = (
        len(catalog.footprints) * (len(catalog.footprints) - 1) // 2
    )
    if len(catalog.relationships) != expected_relationship_count:
        errors.append("relationships must cover every footprint pair exactly once.")

    if len(valid_footprints) != len(catalog.footprints) or policy_errors:
        return tuple(errors)

    expected_pairs = tuple(
        (catalog.footprints[first_index], catalog.footprints[second_index])
        for first_index in range(len(catalog.footprints))
        for second_index in range(first_index + 1, len(catalog.footprints))
    )

    for index, relationship in enumerate(catalog.relationships):
        if not isinstance(relationship, SpatialPairRelationship):
            errors.append(
                f"relationships[{index}] must be a SpatialPairRelationship."
            )
            continue

        relationship_errors = validate_spatial_pair_relationship(
            relationship,
            policy=policy,
        )
        errors.extend(
            f"relationships[{index}].{error}"
            for error in relationship_errors
        )

        if index >= len(expected_pairs):
            continue

        first, second = expected_pairs[index]
        observed_members = (
            relationship.first_pair_id,
            relationship.first_tile_id,
            relationship.second_pair_id,
            relationship.second_tile_id,
        )
        expected_members = (
            first.pair_id,
            first.tile_id,
            second.pair_id,
            second.tile_id,
        )
        if observed_members != expected_members:
            errors.append(
                f"relationships[{index}] must match the footprint pair order."
            )

        expected_geometry = _expected_geometry(first, second, policy)
        observed_geometry = (
            relationship.row_overlap_pixels,
            relationship.column_overlap_pixels,
            relationship.row_gap_pixels,
            relationship.column_gap_pixels,
            relationship.linked,
        )
        if observed_geometry != expected_geometry:
            errors.append(
                f"relationships[{index}] geometry must match its footprints."
            )

    return tuple(errors)


def _expected_components(
    catalog: SpatialRelationshipCatalog,
) -> tuple[tuple[str, ...], ...]:
    pair_ids = tuple(footprint.pair_id for footprint in catalog.footprints)
    index_by_pair_id = {
        pair_id: index
        for index, pair_id in enumerate(pair_ids)
    }
    parents = list(range(len(pair_ids)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first_index: int, second_index: int) -> None:
        first_root = find(first_index)
        second_root = find(second_index)
        if first_root == second_root:
            return

        if first_root < second_root:
            parents[second_root] = first_root
        else:
            parents[first_root] = second_root

    for relationship in catalog.relationships:
        if relationship.linked:
            union(
                index_by_pair_id[relationship.first_pair_id],
                index_by_pair_id[relationship.second_pair_id],
            )

    members_by_root: dict[int, list[str]] = {}
    for index, pair_id in enumerate(pair_ids):
        root = find(index)
        members_by_root.setdefault(root, []).append(pair_id)

    return tuple(
        tuple(members)
        for _, members in sorted(members_by_root.items())
    )


def validate_spatial_leakage_group_catalog(
    catalog: SpatialLeakageGroupCatalog,
    *,
    relationship_catalog: SpatialRelationshipCatalog,
) -> tuple[str, ...]:
    errors: list[str] = []

    if catalog.schema_version != SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION:
        errors.append("schema_version is not supported.")

    if not isinstance(catalog.output_name, str) or not catalog.output_name.strip():
        errors.append("output_name must not be empty.")

    for field_name, value in (
        ("pair_catalog_id", catalog.pair_catalog_id),
        ("relationship_catalog_id", catalog.relationship_catalog_id),
        ("grouping_policy_id", catalog.grouping_policy_id),
    ):
        if not _is_sha256_id(value):
            errors.append(f"{field_name} must be a valid SHA-256 identity.")

    if catalog.pair_catalog_id != relationship_catalog.pair_catalog_id:
        errors.append("pair_catalog_id must match the relationship catalog.")

    expected_relationship_catalog_id = build_spatial_relationship_catalog_id(
        relationship_catalog
    )
    if catalog.relationship_catalog_id != expected_relationship_catalog_id:
        errors.append("relationship_catalog_id must match the relationship catalog.")

    if catalog.grouping_policy_id != relationship_catalog.grouping_policy_id:
        errors.append("grouping_policy_id must match the relationship catalog.")

    if not isinstance(catalog.groups, tuple):
        errors.append("groups must be a tuple.")
        return tuple(errors)

    if not catalog.groups:
        errors.append("groups must not be empty.")
        return tuple(errors)

    valid_groups: list[SpatialLeakageGroup] = []
    for index, group in enumerate(catalog.groups):
        if not isinstance(group, SpatialLeakageGroup):
            errors.append(f"groups[{index}] must be a SpatialLeakageGroup.")
            continue

        valid_groups.append(group)
        group_errors = validate_spatial_leakage_group(group)
        errors.extend(
            f"groups[{index}].{error}"
            for error in group_errors
        )

        expected_group_id = build_spatial_leakage_group_id(
            pair_ids=group.pair_ids,
            tile_ids=group.tile_ids,
        )
        if group.spatial_group_id != expected_group_id:
            errors.append(
                f"groups[{index}].spatial_group_id must match group membership."
            )

    observed_pair_ids = tuple(
        pair_id
        for group in valid_groups
        for pair_id in group.pair_ids
    )
    observed_tile_ids = tuple(
        tile_id
        for group in valid_groups
        for tile_id in group.tile_ids
    )

    if len(set(observed_pair_ids)) != len(observed_pair_ids):
        errors.append("pair_id values must not appear in multiple groups.")

    if len(set(observed_tile_ids)) != len(observed_tile_ids):
        errors.append("tile_id values must not appear in multiple groups.")

    footprints_by_pair_id = {
        footprint.pair_id: footprint
        for footprint in relationship_catalog.footprints
    }
    expected_pair_ids = set(footprints_by_pair_id)
    if set(observed_pair_ids) != expected_pair_ids:
        errors.append("groups must cover every relationship footprint exactly once.")

    for group_index, group in enumerate(valid_groups):
        expected_tile_ids = tuple(
            footprints_by_pair_id[pair_id].tile_id
            for pair_id in group.pair_ids
            if pair_id in footprints_by_pair_id
        )
        if group.tile_ids != expected_tile_ids:
            errors.append(
                f"groups[{group_index}].tile_ids must match its pair_ids."
            )

    expected_components = _expected_components(relationship_catalog)
    observed_components = tuple(group.pair_ids for group in valid_groups)
    if observed_components != expected_components:
        errors.append(
            "groups must match the connected components in footprint order."
        )

    return tuple(errors)