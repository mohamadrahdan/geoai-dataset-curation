from geoai_dataset_curation.spatial_split import (
    SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_footprint(
    pair_character: str,
    tile_character: str,
    *,
    row_offset: int,
    column_offset: int,
) -> SpatialTileFootprint:
    return SpatialTileFootprint(
        pair_id=sha(pair_character),
        tile_id=sha(tile_character),
        row_offset_pixels=row_offset,
        column_offset_pixels=column_offset,
        read_width_pixels=256,
        read_height_pixels=256,
    )


def test_spatial_relationship_schema_versions_are_stable() -> None:
    assert (
        SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION
        == "spatial-relationship-catalog-v1"
    )
    assert (
        SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION
        == "spatial-leakage-group-catalog-v1"
    )


def test_spatial_grouping_policy_uses_explicit_pixel_gap_metric() -> None:
    policy = SpatialGroupingPolicy(
        distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
        maximum_gap_pixels=64,
    )
    assert policy.distance_metric.value == "euclidean_pixel_gap"
    assert policy.maximum_gap_pixels == 64


def test_spatial_tile_footprint_reports_source_extent() -> None:
    footprint = make_footprint(
        "1",
        "4",
        row_offset=192,
        column_offset=384,
    )
    assert footprint.row_stop_pixels == 448
    assert footprint.column_stop_pixels == 640
    assert footprint.source_pixel_count == 65_536


def test_spatial_pair_relationship_reports_overlap_and_gap() -> None:
    overlapping = SpatialPairRelationship(
        first_pair_id=sha("1"),
        first_tile_id=sha("4"),
        second_pair_id=sha("2"),
        second_tile_id=sha("5"),
        row_overlap_pixels=256,
        column_overlap_pixels=64,
        row_gap_pixels=0,
        column_gap_pixels=0,
        linked=True,
    )
    separated = SpatialPairRelationship(
        first_pair_id=sha("1"),
        first_tile_id=sha("4"),
        second_pair_id=sha("3"),
        second_tile_id=sha("6"),
        row_overlap_pixels=0,
        column_overlap_pixels=0,
        row_gap_pixels=30,
        column_gap_pixels=40,
        linked=False,
    )
    assert overlapping.shared_pixel_count == 16_384
    assert overlapping.gap_squared_pixels == 0
    assert overlapping.overlaps_source_pixels is True
    assert separated.shared_pixel_count == 0
    assert separated.gap_squared_pixels == 2_500
    assert separated.overlaps_source_pixels is False


def test_spatial_relationship_catalog_reports_derived_counts() -> None:
    footprints = (
        make_footprint("1", "4", row_offset=0, column_offset=0),
        make_footprint("2", "5", row_offset=0, column_offset=192),
        make_footprint("3", "6", row_offset=500, column_offset=500),
    )
    relationships = (
        SpatialPairRelationship(
            first_pair_id=sha("1"),
            first_tile_id=sha("4"),
            second_pair_id=sha("2"),
            second_tile_id=sha("5"),
            row_overlap_pixels=256,
            column_overlap_pixels=64,
            row_gap_pixels=0,
            column_gap_pixels=0,
            linked=True,
        ),
        SpatialPairRelationship(
            first_pair_id=sha("1"),
            first_tile_id=sha("4"),
            second_pair_id=sha("3"),
            second_tile_id=sha("6"),
            row_overlap_pixels=0,
            column_overlap_pixels=0,
            row_gap_pixels=244,
            column_gap_pixels=244,
            linked=False,
        ),
        SpatialPairRelationship(
            first_pair_id=sha("2"),
            first_tile_id=sha("5"),
            second_pair_id=sha("3"),
            second_tile_id=sha("6"),
            row_overlap_pixels=0,
            column_overlap_pixels=0,
            row_gap_pixels=244,
            column_gap_pixels=52,
            linked=False,
        ),
    )
    catalog = SpatialRelationshipCatalog(
        schema_version=SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
        output_name="relationships-v1",
        pair_catalog_id=sha("a"),
        tile_catalog_id=sha("b"),
        grouping_policy_id=sha("c"),
        footprints=footprints,
        relationships=relationships,
    )
    assert catalog.footprint_count == 3
    assert catalog.relationship_count == 3
    assert catalog.linked_relationship_count == 1
    assert catalog.overlapping_relationship_count == 1


def test_spatial_leakage_group_catalog_reports_derived_counts() -> None:
    catalog = SpatialLeakageGroupCatalog(
        schema_version=SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
        output_name="groups-v1",
        pair_catalog_id=sha("a"),
        relationship_catalog_id=sha("b"),
        grouping_policy_id=sha("c"),
        groups=(
            SpatialLeakageGroup(
                spatial_group_id=sha("d"),
                pair_ids=(sha("1"), sha("2")),
                tile_ids=(sha("4"), sha("5")),
            ),
            SpatialLeakageGroup(
                spatial_group_id=sha("e"),
                pair_ids=(sha("3"),),
                tile_ids=(sha("6"),),
            ),
        ),
    )
    assert catalog.group_count == 2
    assert catalog.pair_count == 3
    assert catalog.largest_group_size == 2
    assert catalog.singleton_group_count == 1