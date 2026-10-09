"Spatial relationship validation."
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialPairRelationship,
    SpatialTileFootprint,
)


def _is_sha256_id(value: object) -> bool:
    if not isinstance(value, str):
        return False

    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_spatial_grouping_policy(
    policy: SpatialGroupingPolicy,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(policy.distance_metric, SpatialDistanceMetric):
        errors.append("distance_metric must be a SpatialDistanceMetric.")

    if not _is_non_negative_int(policy.maximum_gap_pixels):
        errors.append("maximum_gap_pixels must be a non-negative integer.")

    return tuple(errors)


def validate_spatial_tile_footprint(
    footprint: SpatialTileFootprint,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not _is_sha256_id(footprint.pair_id):
        errors.append("pair_id must be a valid SHA-256 identity.")

    if not _is_sha256_id(footprint.tile_id):
        errors.append("tile_id must be a valid SHA-256 identity.")

    for field_name, value in (
        ("row_offset_pixels", footprint.row_offset_pixels),
        ("column_offset_pixels", footprint.column_offset_pixels),
    ):
        if not _is_non_negative_int(value):
            errors.append(f"{field_name} must be a non-negative integer.")

    for field_name, value in (
        ("read_width_pixels", footprint.read_width_pixels),
        ("read_height_pixels", footprint.read_height_pixels),
    ):
        if not _is_positive_int(value):
            errors.append(f"{field_name} must be a positive integer.")

    return tuple(errors)


def validate_spatial_pair_relationship(
    relationship: SpatialPairRelationship,
    *,
    policy: SpatialGroupingPolicy | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []

    for field_name, value in (
        ("first_pair_id", relationship.first_pair_id),
        ("first_tile_id", relationship.first_tile_id),
        ("second_pair_id", relationship.second_pair_id),
        ("second_tile_id", relationship.second_tile_id),
    ):
        if not _is_sha256_id(value):
            errors.append(f"{field_name} must be a valid SHA-256 identity.")

    if relationship.first_pair_id == relationship.second_pair_id:
        errors.append("relationship pair_id values must be distinct.")

    if relationship.first_tile_id == relationship.second_tile_id:
        errors.append("relationship tile_id values must be distinct.")

    for field_name, value in (
        ("row_overlap_pixels", relationship.row_overlap_pixels),
        ("column_overlap_pixels", relationship.column_overlap_pixels),
        ("row_gap_pixels", relationship.row_gap_pixels),
        ("column_gap_pixels", relationship.column_gap_pixels),
    ):
        if not _is_non_negative_int(value):
            errors.append(f"{field_name} must be a non-negative integer.")

    if relationship.row_overlap_pixels > 0 and relationship.row_gap_pixels > 0:
        errors.append("row overlap and row gap cannot both be positive.")

    if (
        relationship.column_overlap_pixels > 0
        and relationship.column_gap_pixels > 0
    ):
        errors.append("column overlap and column gap cannot both be positive.")

    if not isinstance(relationship.linked, bool):
        errors.append("linked must be a boolean.")
    elif relationship.overlaps_source_pixels and not relationship.linked:
        errors.append("overlapping source footprints must be linked.")

    if policy is not None:
        policy_errors = validate_spatial_grouping_policy(policy)
        if not policy_errors and isinstance(relationship.linked, bool):
            maximum_gap_squared = policy.maximum_gap_pixels**2
            expected_linked = relationship.gap_squared_pixels <= maximum_gap_squared
            if relationship.linked != expected_linked:
                errors.append("linked must match the spatial grouping policy.")

    return tuple(errors)


def validate_spatial_leakage_group(
    group: SpatialLeakageGroup,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not _is_sha256_id(group.spatial_group_id):
        errors.append("spatial_group_id must be a valid SHA-256 identity.")

    if not isinstance(group.pair_ids, tuple):
        errors.append("pair_ids must be a tuple.")
    elif not group.pair_ids:
        errors.append("pair_ids must not be empty.")
    else:
        for index, pair_id in enumerate(group.pair_ids):
            if not _is_sha256_id(pair_id):
                errors.append(f"pair_ids[{index}] must be a valid SHA-256 identity.")

        if len(set(group.pair_ids)) != len(group.pair_ids):
            errors.append("pair_ids must be unique within a spatial group.")

    if not isinstance(group.tile_ids, tuple):
        errors.append("tile_ids must be a tuple.")
    elif not group.tile_ids:
        errors.append("tile_ids must not be empty.")
    else:
        for index, tile_id in enumerate(group.tile_ids):
            if not _is_sha256_id(tile_id):
                errors.append(f"tile_ids[{index}] must be a valid SHA-256 identity.")

        if len(set(group.tile_ids)) != len(group.tile_ids):
            errors.append("tile_ids must be unique within a spatial group.")

    if isinstance(group.pair_ids, tuple) and isinstance(group.tile_ids, tuple):
        if len(group.pair_ids) != len(group.tile_ids):
            errors.append("pair_ids and tile_ids must have equal lengths.")

    return tuple(errors)