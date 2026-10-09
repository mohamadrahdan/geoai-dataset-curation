"Build leakage-safe spatial groups."
from geoai_dataset_curation.spatial_split.catalog_validation import (
    validate_spatial_leakage_group_catalog,
    validate_spatial_relationship_catalog,
)
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    SpatialRelationshipCatalog,
)
from geoai_dataset_curation.spatial_split.relationship_identity import (
    build_spatial_leakage_group_id,
    build_spatial_relationship_catalog_id,
)


def _component_indexes(
    catalog: SpatialRelationshipCatalog,
) -> tuple[tuple[int, ...], ...]:
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

    members_by_root: dict[int, list[int]] = {}
    for index in range(len(pair_ids)):
        root = find(index)
        members_by_root.setdefault(root, []).append(index)

    return tuple(
        tuple(members)
        for _, members in sorted(members_by_root.items())
    )


def build_spatial_leakage_group_catalog(
    relationship_catalog: SpatialRelationshipCatalog,
    *,
    policy: SpatialGroupingPolicy,
    output_name: str,
) -> SpatialLeakageGroupCatalog:
    errors = validate_spatial_relationship_catalog(
        relationship_catalog,
        policy=policy,
    )
    if not isinstance(output_name, str) or not output_name.strip():
        errors += ("output_name must not be empty.",)

    if errors:
        raise ValueError("Cannot build spatial leakage groups: " + "; ".join(errors))

    groups = tuple(
        _build_group(relationship_catalog, component)
        for component in _component_indexes(relationship_catalog)
    )
    catalog = SpatialLeakageGroupCatalog(
        schema_version=SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
        output_name=output_name.strip(),
        pair_catalog_id=relationship_catalog.pair_catalog_id,
        relationship_catalog_id=build_spatial_relationship_catalog_id(
            relationship_catalog
        ),
        grouping_policy_id=relationship_catalog.grouping_policy_id,
        groups=groups,
    )

    catalog_errors = validate_spatial_leakage_group_catalog(
        catalog,
        relationship_catalog=relationship_catalog,
    )
    if catalog_errors:
        raise ValueError(
            "Cannot build invalid spatial leakage groups: "
            + "; ".join(catalog_errors)
        )

    return catalog


def _build_group(
    catalog: SpatialRelationshipCatalog,
    component: tuple[int, ...],
) -> SpatialLeakageGroup:
    pair_ids = tuple(
        catalog.footprints[index].pair_id
        for index in component
    )
    tile_ids = tuple(
        catalog.footprints[index].tile_id
        for index in component
    )
    return SpatialLeakageGroup(
        spatial_group_id=build_spatial_leakage_group_id(
            pair_ids=pair_ids,
            tile_ids=tile_ids,
        ),
        pair_ids=pair_ids,
        tile_ids=tile_ids,
    )