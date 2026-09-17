import json
from dataclasses import replace
from pathlib import Path
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    build_image_mask_pair_catalog_id,
    build_image_mask_pair_id,
    build_tile_negative_provenance_catalog_id,
    build_tile_sampling_selection_id,
    image_mask_pair_catalog_to_dict,
    image_mask_pair_record_to_dict,
    select_tile_candidates,
    verify_image_mask_pair_catalog_artifact,
    write_image_mask_pair_catalog,
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


def make_context():
    tile_catalog = TileCatalog(
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
    selection = select_tile_candidates(tile_catalog)
    provenance = TileNegativeProvenanceCatalog(
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

    provenance_by_id = {
        record.tile_id: record
        for record in provenance.records
    }
    pairs: list[ImageMaskPairRecord] = []
    for candidate in selection.selected_candidates:
        provenance_record = provenance_by_id[candidate.tile_id]
        draft = ImageMaskPairRecord(
            pair_id=PLACEHOLDER_PAIR_ID,
            tile_id=candidate.tile_id,
            image_tile_path=f"pairs/images/{candidate.tile_id}.tif",
            mask_tile_path=f"pairs/masks/{candidate.tile_id}.tif",
            label_class=candidate.label_class,
            negative_provenance_kind=provenance_record.kind,
        )
        pairs.append(
            replace(
                draft,
                pair_id=build_image_mask_pair_id(draft),
            )
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
        pairs=tuple(pairs),
    )
    return tile_catalog, selection, provenance, pair_catalog


def test_pair_record_serialization_preserves_fields() -> None:
    _, _, _, pair_catalog = make_context()
    pair = pair_catalog.pairs[0]
    payload = image_mask_pair_record_to_dict(pair)
    assert payload["pair_id"] == pair.pair_id
    assert payload["tile_id"] == pair.tile_id
    assert payload["label_class"] == "positive"
    assert payload["negative_provenance_kind"] == "none"


def test_pair_catalog_serialization_includes_identity_and_counts() -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()

    payload = image_mask_pair_catalog_to_dict(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert payload["pair_catalog_id"] == (
        build_image_mask_pair_catalog_id(pair_catalog)
    )
    assert payload["pair_count"] == 2
    assert payload["positive_pair_count"] == 1
    assert payload["negative_only_pair_count"] == 1
    assert len(payload["pairs"]) == 2


def test_pair_catalog_writer_creates_canonical_json(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()
    output_path = tmp_path / "nested" / "pair-catalog.json"
    result = write_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_path=output_path,
    )
    assert result == output_path
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(
        output_path.read_text(encoding="utf-8")
    ) == image_mask_pair_catalog_to_dict(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )


def test_pair_catalog_verification_accepts_matching_artifact(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()
    output_path = tmp_path / "pair-catalog.json"
    write_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_path=output_path,
    )
    assert verify_image_mask_pair_catalog_artifact(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        artifact_path=output_path,
    ) == ()


def test_pair_catalog_verification_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()
    errors = verify_image_mask_pair_catalog_artifact(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        artifact_path=tmp_path / "missing.json",
    )
    assert errors == (
        "pair catalog artifact does not exist.",
    )


def test_pair_catalog_verification_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()
    output_path = tmp_path / "pair-catalog.json"
    output_path.write_text("{invalid-json", encoding="utf-8")
    errors = verify_image_mask_pair_catalog_artifact(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        artifact_path=output_path,
    )
    assert errors == (
        "pair catalog artifact must contain valid UTF-8 JSON.",
    )


def test_pair_catalog_verification_rejects_changed_content(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = make_context()
    output_path = tmp_path / "pair-catalog.json"

    write_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_path=output_path,
    )
    payload = json.loads(
        output_path.read_text(encoding="utf-8")
    )
    payload["pair_count"] = 99
    output_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    errors = verify_image_mask_pair_catalog_artifact(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        artifact_path=output_path,
    )
    assert errors == (
        "pair catalog artifact content does not match expected pair catalog.",
    )