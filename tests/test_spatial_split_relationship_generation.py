from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split import (
    SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION,
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialSplitInputAcceptance,
    build_spatial_grouping_policy_id,
    build_spatial_relationship_catalog,
    build_spatial_relationship_catalog_id,
    validate_spatial_relationship_inputs,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_tile(
    tile_character: str,
    *,
    row_index: int,
    column_index: int,
    row_offset: int,
    column_offset: int,
) -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id=sha(tile_character),
        grid_id=sha("a"),
        layout_id=sha("b"),
        row_index=row_index,
        column_index=column_index,
        row_offset_pixels=row_offset,
        column_offset_pixels=column_offset,
        read_width_pixels=256,
        read_height_pixels=256,
        output_width_pixels=256,
        output_height_pixels=256,
        left=float(column_offset),
        bottom=float(-(row_offset + 256)),
        right=float(column_offset + 256),
        top=float(-row_offset),
        positive_pixel_count=1,
        negative_pixel_count=1,
        ignore_pixel_count=65_534,
    )


def make_tile_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="tiles-v1",
        image_artifact_path="image.tif",
        label_artifact_path="label.tif",
        grid_id=sha("a"),
        layout_id=sha("b"),
        tiles=(
            make_tile(
                "4",
                row_index=0,
                column_index=0,
                row_offset=0,
                column_offset=0,
            ),
            make_tile(
                "5",
                row_index=0,
                column_index=1,
                row_offset=0,
                column_offset=192,
            ),
            make_tile(
                "6",
                row_index=1,
                column_index=2,
                row_offset=300,
                column_offset=480,
            ),
        ),
    )


def make_pair(
    pair_character: str,
    tile_character: str,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=sha(pair_character),
        tile_id=sha(tile_character),
        image_tile_path=f"images/{pair_character}.tif",
        mask_tile_path=f"masks/{pair_character}.tif",
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=NegativeProvenanceKind.NONE,
    )


def make_pair_catalog(tile_catalog: TileCatalog) -> ImageMaskPairCatalog:
    return ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="pairs-v1",
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        selection_id=sha("c"),
        provenance_catalog_id=sha("d"),
        source_image_artifact_path="image.tif",
        source_label_artifact_path="label.tif",
        pairs=(
            make_pair("1", "4"),
            make_pair("2", "5"),
            make_pair("3", "6"),
        ),
    )


def make_acceptance(
    pair_catalog: ImageMaskPairCatalog,
) -> SpatialSplitInputAcceptance:
    return SpatialSplitInputAcceptance(
        pair_catalog_id=build_image_mask_pair_catalog_id(pair_catalog),
        pair_qc_report_id=sha("e"),
        visual_review_catalog_id=sha("f"),
        pair_ids=tuple(pair.pair_id for pair in pair_catalog.pairs),
        tile_ids=tuple(pair.tile_id for pair in pair_catalog.pairs),
    )


def make_policy(maximum_gap_pixels: int = 64) -> SpatialGroupingPolicy:
    return SpatialGroupingPolicy(
        distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
        maximum_gap_pixels=maximum_gap_pixels,
    )


def make_context() -> tuple[
    SpatialSplitInputAcceptance,
    ImageMaskPairCatalog,
    TileCatalog,
]:
    tile_catalog = make_tile_catalog()
    pair_catalog = make_pair_catalog(tile_catalog)
    return make_acceptance(pair_catalog), pair_catalog, tile_catalog


def test_valid_relationship_inputs_have_no_errors() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    assert validate_spatial_relationship_inputs(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    ) == ()


def test_relationship_catalog_is_complete_and_deterministic() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    catalog = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )
    repeated_catalog = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )

    assert catalog.schema_version == SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION
    assert catalog.pair_catalog_id == acceptance.pair_catalog_id
    assert catalog.tile_catalog_id == build_tile_catalog_id(tile_catalog)
    assert catalog.grouping_policy_id == build_spatial_grouping_policy_id(
        make_policy()
    )
    assert catalog.footprint_count == 3
    assert catalog.relationship_count == 3
    assert catalog.linked_relationship_count == 2
    assert catalog.overlapping_relationship_count == 1
    assert catalog == repeated_catalog
    assert build_spatial_relationship_catalog_id(catalog) == (
        build_spatial_relationship_catalog_id(repeated_catalog)
    )


def test_relationships_follow_accepted_pair_order() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    catalog = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )

    observed_pairs = tuple(
        (relationship.first_pair_id, relationship.second_pair_id)
        for relationship in catalog.relationships
    )
    assert observed_pairs == (
        (sha("1"), sha("2")),
        (sha("1"), sha("3")),
        (sha("2"), sha("3")),
    )


def test_relationship_geometry_uses_source_pixel_footprints() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    catalog = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )
    first_second, first_third, second_third = catalog.relationships

    assert first_second.row_overlap_pixels == 256
    assert first_second.column_overlap_pixels == 64
    assert first_second.shared_pixel_count == 16_384
    assert first_second.linked is True

    assert first_third.row_gap_pixels == 44
    assert first_third.column_gap_pixels == 224
    assert first_third.linked is False

    assert second_third.row_gap_pixels == 44
    assert second_third.column_gap_pixels == 32
    assert second_third.gap_squared_pixels == 2_960
    assert second_third.linked is True


def test_smaller_gap_policy_changes_only_policy_dependent_links() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    catalog = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(maximum_gap_pixels=54),
        output_name="relationships-v1",
    )

    assert tuple(
        relationship.linked
        for relationship in catalog.relationships
    ) == (True, False, False)


def test_input_validation_rejects_reordered_acceptance() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()
    reordered_acceptance = replace(
        acceptance,
        pair_ids=tuple(reversed(acceptance.pair_ids)),
    )

    errors = validate_spatial_relationship_inputs(
        reordered_acceptance,
        pair_catalog=pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )

    assert "acceptance pair_ids must match the pair catalog order." in errors


def test_input_validation_rejects_wrong_tile_catalog() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()
    changed_pair_catalog = replace(pair_catalog, tile_catalog_id=sha("0"))

    errors = validate_spatial_relationship_inputs(
        acceptance,
        pair_catalog=changed_pair_catalog,
        tile_catalog=tile_catalog,
        policy=make_policy(),
        output_name="relationships-v1",
    )

    assert "acceptance pair_catalog_id must match the pair catalog." in errors
    assert "pair catalog tile_catalog_id must match the tile catalog." in errors


def test_invalid_inputs_cannot_build_relationships() -> None:
    acceptance, pair_catalog, tile_catalog = make_context()

    with pytest.raises(
        ValueError,
        match="Cannot build spatial relationships",
    ):
        build_spatial_relationship_catalog(
            acceptance,
            pair_catalog=pair_catalog,
            tile_catalog=tile_catalog,
            policy=make_policy(maximum_gap_pixels=-1),
            output_name="",
        )