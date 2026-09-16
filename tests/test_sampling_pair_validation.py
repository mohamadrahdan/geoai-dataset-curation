from dataclasses import replace
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    build_image_mask_pair_id,
    build_tile_negative_provenance_catalog_id,
    build_tile_sampling_selection_id,
    select_tile_candidates,
    validate_image_mask_pair_catalog,
    validate_image_mask_pair_record,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
PLACEHOLDER_PAIR_ID = "sha256:" + ("0" * 64)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    label_class: TileLabelClass,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 0, 15),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 15),
        TileLabelClass.ALL_IGNORE: (0, 0, 16),
    }
    positive, negative, ignore = counts[label_class]
    left = float(row_index * 40)
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 4,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=left,
        bottom=0.0,
        right=left + 40.0,
        top=40.0,
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def make_tile_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="pair-candidates",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(
            make_candidate(
                digest_character="c",
                row_index=0,
                label_class=TileLabelClass.POSITIVE,
            ),
            make_candidate(
                digest_character="d",
                row_index=1,
                label_class=TileLabelClass.NEGATIVE_ONLY,
            ),
            make_candidate(
                digest_character="e",
                row_index=2,
                label_class=TileLabelClass.ALL_IGNORE,
            ),
        ),
    )


def make_provenance_catalog(
    tile_catalog: TileCatalog,
) -> TileNegativeProvenanceCatalog:
    return TileNegativeProvenanceCatalog(
        schema_version=TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        records=(
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[0].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[1].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=1,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[2].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
        ),
    )


def make_pair(
    candidate: TileCandidateRecord,
    provenance: TileNegativeProvenance,
) -> ImageMaskPairRecord:
    draft = ImageMaskPairRecord(
        pair_id=PLACEHOLDER_PAIR_ID,
        tile_id=candidate.tile_id,
        image_tile_path=f"pairs/images/{candidate.tile_id}.tif",
        mask_tile_path=f"pairs/masks/{candidate.tile_id}.tif",
        label_class=candidate.label_class,
        negative_provenance_kind=provenance.kind,
    )
    return replace(
        draft,
        pair_id=build_image_mask_pair_id(draft),
    )


def make_pair_catalog():
    tile_catalog = make_tile_catalog()
    selection = select_tile_candidates(tile_catalog)
    provenance = make_provenance_catalog(tile_catalog)
    provenance_by_id = {
        record.tile_id: record
        for record in provenance.records
    }
    pairs = tuple(
        make_pair(
            candidate,
            provenance_by_id[candidate.tile_id],
        )
        for candidate in selection.selected_candidates
    )
    pair_catalog = ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="loop1-image-mask-pairs",
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        selection_id=build_tile_sampling_selection_id(
            selection,
            catalog=tile_catalog,
        ),
        provenance_catalog_id=(
            build_tile_negative_provenance_catalog_id(
                provenance,
                catalog=tile_catalog,
            )
        ),
        source_image_artifact_path=(
            tile_catalog.image_artifact_path
        ),
        source_label_artifact_path=(
            tile_catalog.label_artifact_path
        ),
        pairs=pairs,
    )
    return tile_catalog, selection, provenance, pair_catalog


def test_pair_record_validation_accepts_matching_evidence() -> None:
    tile_catalog, _, provenance, pair_catalog = make_pair_catalog()
    assert validate_image_mask_pair_record(
        pair_catalog.pairs[0],
        candidate=tile_catalog.tiles[0],
        provenance=provenance.records[0],
    ) == ()


def test_pair_catalog_validation_accepts_complete_ordered_pairs() -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_pair_catalog()
    )
    assert validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    ) == ()


def test_pair_validation_rejects_wrong_pair_identity() -> None:
    tile_catalog, _, provenance, pair_catalog = make_pair_catalog()
    invalid = replace(
        pair_catalog.pairs[0],
        pair_id=PLACEHOLDER_PAIR_ID,
    )
    errors = validate_image_mask_pair_record(
        invalid,
        candidate=tile_catalog.tiles[0],
        provenance=provenance.records[0],
    )
    assert "pair_id must match the pair identity payload." in errors


def test_pair_validation_rejects_wrong_label_class() -> None:
    tile_catalog, _, provenance, pair_catalog = make_pair_catalog()
    invalid = replace(
        pair_catalog.pairs[0],
        label_class=TileLabelClass.NEGATIVE_ONLY,
    )
    errors = validate_image_mask_pair_record(
        invalid,
        candidate=tile_catalog.tiles[0],
        provenance=provenance.records[0],
    )
    assert "label_class must match the selected candidate." in errors


def test_pair_validation_rejects_wrong_provenance_kind() -> None:
    tile_catalog, _, provenance, pair_catalog = make_pair_catalog()
    invalid = replace(
        pair_catalog.pairs[1],
        negative_provenance_kind=NegativeProvenanceKind.NONE,
    )
    errors = validate_image_mask_pair_record(
        invalid,
        candidate=tile_catalog.tiles[1],
        provenance=provenance.records[1],
    )
    assert (
        "negative_provenance_kind must match the tile provenance."
        in errors
    )


def test_pair_validation_rejects_all_ignore_candidate() -> None:
    tile_catalog = make_tile_catalog()
    provenance = make_provenance_catalog(tile_catalog)
    pair = make_pair(
        tile_catalog.tiles[2],
        provenance.records[2],
    )
    errors = validate_image_mask_pair_record(
        pair,
        candidate=tile_catalog.tiles[2],
        provenance=provenance.records[2],
    )
    assert "all-ignore candidates must not produce pairs." in errors


def test_catalog_validation_rejects_incomplete_pair_population() -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_pair_catalog()
    )
    invalid = replace(
        pair_catalog,
        pairs=pair_catalog.pairs[:-1],
    )
    errors = validate_image_mask_pair_catalog(
        invalid,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )

    assert (
        "pairs must cover every selected tile in selection order."
        in errors
    )


def test_catalog_validation_rejects_wrong_selection_identity() -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_pair_catalog()
    )
    invalid = replace(
        pair_catalog,
        selection_id="sha256:" + ("9" * 64),
    )
    errors = validate_image_mask_pair_catalog(
        invalid,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert (
        "selection_id must match the sampling selection."
        in errors
    )


def test_catalog_validation_rejects_duplicate_image_paths() -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_pair_catalog()
    )
    changed_draft = replace(
        pair_catalog.pairs[1],
        image_tile_path=pair_catalog.pairs[0].image_tile_path,
    )
    changed = replace(
        changed_draft,
        pair_id=build_image_mask_pair_id(changed_draft),
    )
    invalid = replace(
        pair_catalog,
        pairs=(
            pair_catalog.pairs[0],
            changed,
        ),
    )
    errors = validate_image_mask_pair_catalog(
        invalid,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert "image tile paths must be unique." in errors