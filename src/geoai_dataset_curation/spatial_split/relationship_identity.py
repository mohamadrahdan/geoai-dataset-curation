"Stable identities for spatial relationships."
from typing import Any
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SPATIAL_GROUPING_POLICY_SCHEMA_VERSION,
    SPATIAL_LEAKAGE_GROUP_SCHEMA_VERSION,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
)
from geoai_dataset_curation.spatial_split.relationship_validation import (
    validate_spatial_grouping_policy,
)
from geoai_dataset_curation.tiling.identity import _build_sha256_id


def spatial_grouping_policy_identity_payload(
    policy: SpatialGroupingPolicy,
) -> dict[str, Any]:
    errors = validate_spatial_grouping_policy(policy)
    if errors:
        raise ValueError("Cannot identify invalid grouping policy: " + "; ".join(errors))

    return {
        "schema_version": SPATIAL_GROUPING_POLICY_SCHEMA_VERSION,
        "distance_metric": policy.distance_metric.value,
        "maximum_gap_pixels": policy.maximum_gap_pixels,
    }


def build_spatial_grouping_policy_id(policy: SpatialGroupingPolicy) -> str:
    return _build_sha256_id(spatial_grouping_policy_identity_payload(policy))


def spatial_tile_footprint_identity_payload(
    footprint: SpatialTileFootprint,
) -> dict[str, Any]:
    return {
        "pair_id": footprint.pair_id,
        "tile_id": footprint.tile_id,
        "row_offset_pixels": footprint.row_offset_pixels,
        "column_offset_pixels": footprint.column_offset_pixels,
        "read_width_pixels": footprint.read_width_pixels,
        "read_height_pixels": footprint.read_height_pixels,
    }


def spatial_pair_relationship_identity_payload(
    relationship: SpatialPairRelationship,
) -> dict[str, Any]:
    return {
        "first_pair_id": relationship.first_pair_id,
        "first_tile_id": relationship.first_tile_id,
        "second_pair_id": relationship.second_pair_id,
        "second_tile_id": relationship.second_tile_id,
        "row_overlap_pixels": relationship.row_overlap_pixels,
        "column_overlap_pixels": relationship.column_overlap_pixels,
        "row_gap_pixels": relationship.row_gap_pixels,
        "column_gap_pixels": relationship.column_gap_pixels,
        "linked": relationship.linked,
    }


def spatial_relationship_catalog_identity_payload(
    catalog: SpatialRelationshipCatalog,
) -> dict[str, Any]:
    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "pair_catalog_id": catalog.pair_catalog_id,
        "tile_catalog_id": catalog.tile_catalog_id,
        "grouping_policy_id": catalog.grouping_policy_id,
        "footprints": [
            spatial_tile_footprint_identity_payload(footprint)
            for footprint in catalog.footprints
        ],
        "relationships": [
            spatial_pair_relationship_identity_payload(relationship)
            for relationship in catalog.relationships
        ],
    }


def build_spatial_relationship_catalog_id(
    catalog: SpatialRelationshipCatalog,
) -> str:
    return _build_sha256_id(spatial_relationship_catalog_identity_payload(catalog))


def spatial_leakage_group_membership_payload(
    *,
    pair_ids: tuple[str, ...],
    tile_ids: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "schema_version": SPATIAL_LEAKAGE_GROUP_SCHEMA_VERSION,
        "pair_ids": list(pair_ids),
        "tile_ids": list(tile_ids),
    }


def build_spatial_leakage_group_id(
    *,
    pair_ids: tuple[str, ...],
    tile_ids: tuple[str, ...],
) -> str:
    payload = spatial_leakage_group_membership_payload(
        pair_ids=pair_ids,
        tile_ids=tile_ids,
    )
    return _build_sha256_id(payload)


def spatial_leakage_group_identity_payload(
    group: SpatialLeakageGroup,
) -> dict[str, Any]:
    return {
        "spatial_group_id": group.spatial_group_id,
        **spatial_leakage_group_membership_payload(
            pair_ids=group.pair_ids,
            tile_ids=group.tile_ids,
        ),
    }


def spatial_leakage_group_catalog_identity_payload(
    catalog: SpatialLeakageGroupCatalog,
) -> dict[str, Any]:
    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "pair_catalog_id": catalog.pair_catalog_id,
        "relationship_catalog_id": catalog.relationship_catalog_id,
        "grouping_policy_id": catalog.grouping_policy_id,
        "groups": [
            spatial_leakage_group_identity_payload(group)
            for group in catalog.groups
        ],
    }


def build_spatial_leakage_group_catalog_id(
    catalog: SpatialLeakageGroupCatalog,
) -> str:
    return _build_sha256_id(
        spatial_leakage_group_catalog_identity_payload(catalog)
    )