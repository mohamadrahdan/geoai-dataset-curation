from dataclasses import replace
from geoai_dataset_curation.spatial_split import (
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialPairRelationship,
    SpatialRelationshipCatalog,
    SpatialTileFootprint,
    build_spatial_grouping_policy_id,
    build_spatial_relationship_catalog_id,
    spatial_grouping_policy_identity_payload,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_policy(maximum_gap_pixels: int = 64) -> SpatialGroupingPolicy:
    return SpatialGroupingPolicy(
        distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
        maximum_gap_pixels=maximum_gap_pixels,
    )


def make_catalog() -> SpatialRelationshipCatalog:
    return SpatialRelationshipCatalog(
        schema_version=SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
        output_name="relationships-v1",
        pair_catalog_id=sha("a"),
        tile_catalog_id=sha("b"),
        grouping_policy_id=build_spatial_grouping_policy_id(make_policy()),
        footprints=(
            SpatialTileFootprint(
                pair_id=sha("1"),
                tile_id=sha("4"),
                row_offset_pixels=0,
                column_offset_pixels=0,
                read_width_pixels=256,
                read_height_pixels=256,
            ),
            SpatialTileFootprint(
                pair_id=sha("2"),
                tile_id=sha("5"),
                row_offset_pixels=0,
                column_offset_pixels=192,
                read_width_pixels=256,
                read_height_pixels=256,
            ),
        ),
        relationships=(
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
        ),
    )


def test_grouping_policy_identity_is_stable_and_semantic() -> None:
    policy = make_policy()
    assert build_spatial_grouping_policy_id(policy) == (
        build_spatial_grouping_policy_id(policy)
    )
    assert build_spatial_grouping_policy_id(policy) != (
        build_spatial_grouping_policy_id(make_policy(maximum_gap_pixels=65))
    )

    payload = spatial_grouping_policy_identity_payload(policy)
    assert payload == {
        "schema_version": "spatial-grouping-policy-v1",
        "distance_metric": "euclidean_pixel_gap",
        "maximum_gap_pixels": 64,
    }


def test_invalid_grouping_policy_cannot_receive_an_identity() -> None:
    invalid_policy = replace(make_policy(), maximum_gap_pixels=-1)
    try:
        build_spatial_grouping_policy_id(invalid_policy)
    except ValueError as error:
        assert "Cannot identify invalid grouping policy" in str(error)
    else:
        raise AssertionError("Expected invalid grouping policy to be rejected.")


def test_relationship_catalog_identity_changes_with_semantic_content() -> None:
    catalog = make_catalog()
    changed_relationship = replace(catalog.relationships[0], linked=False)
    changed_catalog = replace(catalog, relationships=(changed_relationship,))

    assert build_spatial_relationship_catalog_id(catalog) == (
        build_spatial_relationship_catalog_id(catalog)
    )
    assert build_spatial_relationship_catalog_id(catalog) != (
        build_spatial_relationship_catalog_id(changed_catalog)
    )