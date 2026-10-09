"Build pairwise spatial relationships."
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split.contracts import (
    SpatialSplitInputAcceptance,
)
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialGroupingPolicy,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
)
from geoai_dataset_curation.spatial_split.relationship_identity import (
    build_spatial_grouping_policy_id,
)
from geoai_dataset_curation.spatial_split.relationship_validation import (
    validate_spatial_grouping_policy,
    validate_spatial_pair_relationship,
    validate_spatial_tile_footprint,
)
from geoai_dataset_curation.tiling import (
    TileCandidateRecord,
    TileCatalog,
    build_tile_catalog_id,
    validate_tile_catalog,
)


def validate_spatial_relationship_inputs(
    acceptance: SpatialSplitInputAcceptance,
    *,
    pair_catalog: ImageMaskPairCatalog,
    tile_catalog: TileCatalog,
    policy: SpatialGroupingPolicy,
    output_name: str,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(output_name, str) or not output_name.strip():
        errors.append("output_name must not be empty.")

    policy_errors = validate_spatial_grouping_policy(policy)
    errors.extend(f"policy.{error}" for error in policy_errors)

    tile_catalog_errors = validate_tile_catalog(tile_catalog)
    errors.extend(f"tile_catalog.{error}" for error in tile_catalog_errors)

    expected_pair_catalog_id = build_image_mask_pair_catalog_id(pair_catalog)
    if acceptance.pair_catalog_id != expected_pair_catalog_id:
        errors.append("acceptance pair_catalog_id must match the pair catalog.")

    catalog_pair_ids = tuple(pair.pair_id for pair in pair_catalog.pairs)
    catalog_tile_ids = tuple(pair.tile_id for pair in pair_catalog.pairs)

    if acceptance.pair_ids != catalog_pair_ids:
        errors.append("acceptance pair_ids must match the pair catalog order.")

    if acceptance.tile_ids != catalog_tile_ids:
        errors.append("acceptance tile_ids must match the pair catalog order.")

    if not tile_catalog_errors:
        expected_tile_catalog_id = build_tile_catalog_id(tile_catalog)
        if pair_catalog.tile_catalog_id != expected_tile_catalog_id:
            errors.append("pair catalog tile_catalog_id must match the tile catalog.")

    available_tile_ids = {tile.tile_id for tile in tile_catalog.tiles}
    missing_tile_ids = tuple(
        tile_id
        for tile_id in acceptance.tile_ids
        if tile_id not in available_tile_ids
    )
    if missing_tile_ids:
        errors.append("every accepted tile_id must exist in the tile catalog.")

    return tuple(errors)


def _build_footprint(
    *,
    pair_id: str,
    tile: TileCandidateRecord,
) -> SpatialTileFootprint:
    return SpatialTileFootprint(
        pair_id=pair_id,
        tile_id=tile.tile_id,
        row_offset_pixels=tile.row_offset_pixels,
        column_offset_pixels=tile.column_offset_pixels,
        read_width_pixels=tile.read_width_pixels,
        read_height_pixels=tile.read_height_pixels,
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


def _build_relationship(
    first: SpatialTileFootprint,
    second: SpatialTileFootprint,
    *,
    policy: SpatialGroupingPolicy,
) -> SpatialPairRelationship:
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

    return SpatialPairRelationship(
        first_pair_id=first.pair_id,
        first_tile_id=first.tile_id,
        second_pair_id=second.pair_id,
        second_tile_id=second.tile_id,
        row_overlap_pixels=row_overlap,
        column_overlap_pixels=column_overlap,
        row_gap_pixels=row_gap,
        column_gap_pixels=column_gap,
        linked=linked,
    )


def build_spatial_relationship_catalog(
    acceptance: SpatialSplitInputAcceptance,
    *,
    pair_catalog: ImageMaskPairCatalog,
    tile_catalog: TileCatalog,
    policy: SpatialGroupingPolicy,
    output_name: str,
) -> SpatialRelationshipCatalog:
    errors = validate_spatial_relationship_inputs(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=policy,
        output_name=output_name,
    )
    if errors:
        raise ValueError("Cannot build spatial relationships: " + "; ".join(errors))

    tiles_by_id = {tile.tile_id: tile for tile in tile_catalog.tiles}
    footprints = tuple(
        _build_footprint(
            pair_id=pair_id,
            tile=tiles_by_id[tile_id],
        )
        for pair_id, tile_id in zip(
            acceptance.pair_ids,
            acceptance.tile_ids,
            strict=True,
        )
    )

    relationships = tuple(
        _build_relationship(
            footprints[first_index],
            footprints[second_index],
            policy=policy,
        )
        for first_index in range(len(footprints))
        for second_index in range(first_index + 1, len(footprints))
    )

    footprint_errors = tuple(
        f"footprints[{index}].{error}"
        for index, footprint in enumerate(footprints)
        for error in validate_spatial_tile_footprint(footprint)
    )
    relationship_errors = tuple(
        f"relationships[{index}].{error}"
        for index, relationship in enumerate(relationships)
        for error in validate_spatial_pair_relationship(relationship, policy=policy)
    )
    output_errors = footprint_errors + relationship_errors
    if output_errors:
        raise ValueError(
            "Cannot build invalid spatial relationships: " + "; ".join(output_errors)
        )

    return SpatialRelationshipCatalog(
        schema_version=SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
        output_name=output_name.strip(),
        pair_catalog_id=acceptance.pair_catalog_id,
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        grouping_policy_id=build_spatial_grouping_policy_id(policy),
        footprints=footprints,
        relationships=relationships,
    )