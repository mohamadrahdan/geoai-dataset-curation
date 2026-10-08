from dataclasses import replace
from geoai_dataset_curation.spatial_split import (
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialLeakageGroup,
    SpatialPairRelationship,
    SpatialTileFootprint,
    validate_spatial_grouping_policy,
    validate_spatial_leakage_group,
    validate_spatial_pair_relationship,
    validate_spatial_tile_footprint,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_policy(maximum_gap_pixels: int = 64) -> SpatialGroupingPolicy:
    return SpatialGroupingPolicy(
        distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
        maximum_gap_pixels=maximum_gap_pixels,
    )


def make_footprint() -> SpatialTileFootprint:
    return SpatialTileFootprint(
        pair_id=sha("1"),
        tile_id=sha("4"),
        row_offset_pixels=192,
        column_offset_pixels=384,
        read_width_pixels=256,
        read_height_pixels=256,
    )


def make_relationship(
    *,
    row_gap_pixels: int = 0,
    column_gap_pixels: int = 0,
    row_overlap_pixels: int = 64,
    column_overlap_pixels: int = 64,
    linked: bool = True,
) -> SpatialPairRelationship:
    return SpatialPairRelationship(
        first_pair_id=sha("1"),
        first_tile_id=sha("4"),
        second_pair_id=sha("2"),
        second_tile_id=sha("5"),
        row_overlap_pixels=row_overlap_pixels,
        column_overlap_pixels=column_overlap_pixels,
        row_gap_pixels=row_gap_pixels,
        column_gap_pixels=column_gap_pixels,
        linked=linked,
    )


def test_valid_spatial_relationship_contracts_have_no_errors() -> None:
    assert validate_spatial_grouping_policy(make_policy()) == ()
    assert validate_spatial_tile_footprint(make_footprint()) == ()
    assert validate_spatial_pair_relationship(
        make_relationship(),
        policy=make_policy(),
    ) == ()
    assert validate_spatial_leakage_group(
        SpatialLeakageGroup(
            spatial_group_id=sha("a"),
            pair_ids=(sha("1"), sha("2")),
            tile_ids=(sha("4"), sha("5")),
        )
    ) == ()


def test_grouping_policy_rejects_invalid_values() -> None:
    invalid_policy = SpatialGroupingPolicy(
        distance_metric="euclidean_pixel_gap",  # type: ignore[arg-type]
        maximum_gap_pixels=-1,
    )

    assert validate_spatial_grouping_policy(invalid_policy) == (
        "distance_metric must be a SpatialDistanceMetric.",
        "maximum_gap_pixels must be a non-negative integer.",
    )


def test_footprint_rejects_invalid_identity_and_extent_values() -> None:
    invalid_footprint = replace(
        make_footprint(),
        pair_id="pair",
        row_offset_pixels=-1,
        read_width_pixels=0,
    )

    assert validate_spatial_tile_footprint(invalid_footprint) == (
        "pair_id must be a valid SHA-256 identity.",
        "row_offset_pixels must be a non-negative integer.",
        "read_width_pixels must be a positive integer.",
    )


def test_relationship_rejects_duplicate_members() -> None:
    invalid_relationship = replace(
        make_relationship(),
        second_pair_id=sha("1"),
        second_tile_id=sha("4"),
    )

    errors = validate_spatial_pair_relationship(invalid_relationship)

    assert "relationship pair_id values must be distinct." in errors
    assert "relationship tile_id values must be distinct." in errors


def test_relationship_rejects_simultaneous_axis_overlap_and_gap() -> None:
    invalid_relationship = make_relationship(
        row_overlap_pixels=10,
        column_overlap_pixels=10,
        row_gap_pixels=5,
        column_gap_pixels=6,
    )

    assert validate_spatial_pair_relationship(invalid_relationship) == (
        "row overlap and row gap cannot both be positive.",
        "column overlap and column gap cannot both be positive.",
    )


def test_overlapping_source_footprints_must_be_linked() -> None:
    invalid_relationship = replace(make_relationship(), linked=False)

    assert validate_spatial_pair_relationship(invalid_relationship) == (
        "overlapping source footprints must be linked.",
    )


def test_relationship_link_must_match_grouping_policy() -> None:
    relationship = make_relationship(
        row_overlap_pixels=0,
        column_overlap_pixels=0,
        row_gap_pixels=30,
        column_gap_pixels=40,
        linked=True,
    )

    assert validate_spatial_pair_relationship(
        relationship,
        policy=make_policy(maximum_gap_pixels=49),
    ) == (
        "linked must match the spatial grouping policy.",
    )

    assert validate_spatial_pair_relationship(
        relationship,
        policy=make_policy(maximum_gap_pixels=50),
    ) == ()


def test_leakage_group_rejects_mismatched_and_duplicate_members() -> None:
    invalid_group = SpatialLeakageGroup(
        spatial_group_id=sha("a"),
        pair_ids=(sha("1"), sha("1")),
        tile_ids=(sha("4"),),
    )
    assert validate_spatial_leakage_group(invalid_group) == (
        "pair_ids must be unique within a spatial group.",
        "pair_ids and tile_ids must have equal lengths.",
    )