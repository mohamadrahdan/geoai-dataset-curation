from dataclasses import replace
import pytest
from geoai_dataset_curation.spatial_split import (
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
    build_spatial_grouping_policy_id,
    build_spatial_leakage_group_catalog,
    build_spatial_leakage_group_catalog_id,
    build_spatial_leakage_group_id,
    validate_spatial_leakage_group_catalog,
    validate_spatial_relationship_catalog,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_policy() -> SpatialGroupingPolicy:
    return SpatialGroupingPolicy(
        distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
        maximum_gap_pixels=2,
    )


def make_footprint(
    pair_character: str,
    tile_character: str,
    column_offset: int,
) -> SpatialTileFootprint:
    return SpatialTileFootprint(
        pair_id=sha(pair_character),
        tile_id=sha(tile_character),
        row_offset_pixels=0,
        column_offset_pixels=column_offset,
        read_width_pixels=10,
        read_height_pixels=10,
    )


def make_relationship(
    first: SpatialTileFootprint,
    second: SpatialTileFootprint,
) -> SpatialPairRelationship:
    row_overlap = max(
        0,
        min(first.row_stop_pixels, second.row_stop_pixels)
        - max(first.row_offset_pixels, second.row_offset_pixels),
    )
    column_overlap = max(
        0,
        min(first.column_stop_pixels, second.column_stop_pixels)
        - max(first.column_offset_pixels, second.column_offset_pixels),
    )
    row_gap = 0 if row_overlap > 0 else max(
        first.row_offset_pixels - second.row_stop_pixels,
        second.row_offset_pixels - first.row_stop_pixels,
        0,
    )
    column_gap = 0 if column_overlap > 0 else max(
        first.column_offset_pixels - second.column_stop_pixels,
        second.column_offset_pixels - first.column_stop_pixels,
        0,
    )

    return SpatialPairRelationship(
        first_pair_id=first.pair_id,
        first_tile_id=first.tile_id,
        second_pair_id=second.pair_id,
        second_tile_id=second.tile_id,
        row_overlap_pixels=row_overlap,
        column_overlap_pixels=column_overlap,
        row_gap_pixels=row_gap,
        column_gap_pixels=column_gap,
        linked=row_gap**2 + column_gap**2 <= 4,
    )


def make_relationship_catalog() -> SpatialRelationshipCatalog:
    footprints = (
        make_footprint("1", "5", 0),
        make_footprint("2", "6", 12),
        make_footprint("3", "7", 24),
        make_footprint("4", "8", 100),
    )
    relationships = tuple(
        make_relationship(footprints[first_index], footprints[second_index])
        for first_index in range(len(footprints))
        for second_index in range(first_index + 1, len(footprints))
    )
    return SpatialRelationshipCatalog(
        schema_version=SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
        output_name="relationships-v1",
        pair_catalog_id=sha("a"),
        tile_catalog_id=sha("b"),
        grouping_policy_id=build_spatial_grouping_policy_id(make_policy()),
        footprints=footprints,
        relationships=relationships,
    )


def test_valid_relationship_catalog_has_no_errors() -> None:
    catalog = make_relationship_catalog()

    assert validate_spatial_relationship_catalog(
        catalog,
        policy=make_policy(),
    ) == ()


def test_group_generation_builds_connected_components() -> None:
    relationship_catalog = make_relationship_catalog()

    catalog = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    assert catalog.group_count == 2
    assert catalog.pair_count == 4
    assert catalog.largest_group_size == 3
    assert catalog.singleton_group_count == 1
    assert tuple(group.pair_ids for group in catalog.groups) == (
        (sha("1"), sha("2"), sha("3")),
        (sha("4"),),
    )
    assert tuple(group.tile_ids for group in catalog.groups) == (
        (sha("5"), sha("6"), sha("7")),
        (sha("8"),),
    )


def test_group_generation_is_deterministic() -> None:
    relationship_catalog = make_relationship_catalog()

    first = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    second = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    assert first == second
    assert build_spatial_leakage_group_catalog_id(first) == (
        build_spatial_leakage_group_catalog_id(second)
    )
    assert first.groups[0].spatial_group_id == build_spatial_leakage_group_id(
        pair_ids=(sha("1"), sha("2"), sha("3")),
        tile_ids=(sha("5"), sha("6"), sha("7")),
    )


def test_generated_group_catalog_passes_validation() -> None:
    relationship_catalog = make_relationship_catalog()
    catalog = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    assert validate_spatial_leakage_group_catalog(
        catalog,
        relationship_catalog=relationship_catalog,
    ) == ()


def test_relationship_catalog_rejects_tampered_geometry() -> None:
    catalog = make_relationship_catalog()
    changed_relationship = replace(
        catalog.relationships[0],
        column_gap_pixels=3,
        linked=False,
    )
    changed_catalog = replace(
        catalog,
        relationships=(changed_relationship,) + catalog.relationships[1:],
    )

    errors = validate_spatial_relationship_catalog(
        changed_catalog,
        policy=make_policy(),
    )
    assert "relationships[0] geometry must match its footprints." in errors


def test_group_validation_rejects_merged_components() -> None:
    relationship_catalog = make_relationship_catalog()
    catalog = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    pair_ids = tuple(
        footprint.pair_id
        for footprint in relationship_catalog.footprints
    )
    tile_ids = tuple(
        footprint.tile_id
        for footprint in relationship_catalog.footprints
    )
    merged_group = SpatialLeakageGroup(
        spatial_group_id=build_spatial_leakage_group_id(
            pair_ids=pair_ids,
            tile_ids=tile_ids,
        ),
        pair_ids=pair_ids,
        tile_ids=tile_ids,
    )
    changed_catalog = replace(catalog, groups=(merged_group,))

    errors = validate_spatial_leakage_group_catalog(
        changed_catalog,
        relationship_catalog=relationship_catalog,
    )
    assert (
        "groups must match the connected components in footprint order."
        in errors
    )


def test_group_validation_rejects_wrong_group_identity() -> None:
    relationship_catalog = make_relationship_catalog()
    catalog = build_spatial_leakage_group_catalog(
        relationship_catalog,
        policy=make_policy(),
        output_name="groups-v1",
    )
    changed_group = replace(
        catalog.groups[0],
        spatial_group_id=sha("0"),
    )
    changed_catalog = replace(
        catalog,
        groups=(changed_group, catalog.groups[1]),
    )

    errors = validate_spatial_leakage_group_catalog(
        changed_catalog,
        relationship_catalog=relationship_catalog,
    )
    assert (
        "groups[0].spatial_group_id must match group membership."
        in errors
    )


def test_invalid_relationship_catalog_cannot_build_groups() -> None:
    relationship_catalog = replace(
        make_relationship_catalog(),
        grouping_policy_id=sha("0"),
    )

    with pytest.raises(
        ValueError,
        match="Cannot build spatial leakage groups",
    ):
        build_spatial_leakage_group_catalog(
            relationship_catalog,
            policy=make_policy(),
            output_name="groups-v1",
        )