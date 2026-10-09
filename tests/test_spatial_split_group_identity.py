from dataclasses import replace
from geoai_dataset_curation.spatial_split import (
    SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    build_spatial_leakage_group_catalog_id,
    build_spatial_leakage_group_id,
    spatial_leakage_group_membership_payload,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_group() -> SpatialLeakageGroup:
    pair_ids = (sha("1"), sha("2"))
    tile_ids = (sha("4"), sha("5"))
    return SpatialLeakageGroup(
        spatial_group_id=build_spatial_leakage_group_id(
            pair_ids=pair_ids,
            tile_ids=tile_ids,
        ),
        pair_ids=pair_ids,
        tile_ids=tile_ids,
    )


def make_catalog() -> SpatialLeakageGroupCatalog:
    return SpatialLeakageGroupCatalog(
        schema_version=SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
        output_name="groups-v1",
        pair_catalog_id=sha("a"),
        relationship_catalog_id=sha("b"),
        grouping_policy_id=sha("c"),
        groups=(make_group(),),
    )


def test_group_identity_is_stable_and_membership_based() -> None:
    group = make_group()

    assert group.spatial_group_id == build_spatial_leakage_group_id(
        pair_ids=group.pair_ids,
        tile_ids=group.tile_ids,
    )
    assert group.spatial_group_id != build_spatial_leakage_group_id(
        pair_ids=tuple(reversed(group.pair_ids)),
        tile_ids=tuple(reversed(group.tile_ids)),
    )
    assert spatial_leakage_group_membership_payload(
        pair_ids=group.pair_ids,
        tile_ids=group.tile_ids,
    ) == {
        "schema_version": "spatial-leakage-group-v1",
        "pair_ids": [sha("1"), sha("2")],
        "tile_ids": [sha("4"), sha("5")],
    }


def test_group_catalog_identity_changes_with_semantic_content() -> None:
    catalog = make_catalog()
    changed_catalog = replace(catalog, output_name="groups-v2")
    assert build_spatial_leakage_group_catalog_id(catalog) == (
        build_spatial_leakage_group_catalog_id(catalog)
    )
    assert build_spatial_leakage_group_catalog_id(catalog) != (
        build_spatial_leakage_group_catalog_id(changed_catalog)
    )