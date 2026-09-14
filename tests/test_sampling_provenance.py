from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    NegativeProvenanceKind,
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    validate_tile_negative_provenance,
    validate_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    negative_pixel_count: int,
) -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 2,
        column_offset_pixels=0,
        read_width_pixels=2,
        read_height_pixels=2,
        output_width_pixels=2,
        output_height_pixels=2,
        left=0.0,
        bottom=float(row_index * 20),
        right=20.0,
        top=float((row_index + 1) * 20),
        positive_pixel_count=0,
        negative_pixel_count=negative_pixel_count,
        ignore_pixel_count=4 - negative_pixel_count,
    )


def make_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="negative-provenance-candidates",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(
            make_candidate(
                digest_character="c",
                row_index=0,
                negative_pixel_count=2,
            ),
            make_candidate(
                digest_character="d",
                row_index=1,
                negative_pixel_count=1,
            ),
            make_candidate(
                digest_character="e",
                row_index=2,
                negative_pixel_count=0,
            ),
        ),
    )


def make_provenance_catalog() -> TileNegativeProvenanceCatalog:
    catalog = make_catalog()

    return TileNegativeProvenanceCatalog(
        schema_version=(
            TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION
        ),
        tile_catalog_id=build_tile_catalog_id(catalog),
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        records=(
            TileNegativeProvenance(
                tile_id=catalog.tiles[0].tile_id,
                ordinary_negative_pixel_count=2,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=catalog.tiles[1].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=1,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=catalog.tiles[2].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("record", "expected_kind"),
    [
        (
            TileNegativeProvenance(
                tile_id="tile",
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            NegativeProvenanceKind.NONE,
        ),
        (
            TileNegativeProvenance(
                tile_id="tile",
                ordinary_negative_pixel_count=2,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            NegativeProvenanceKind.ORDINARY_NEGATIVE,
        ),
        (
            TileNegativeProvenance(
                tile_id="tile",
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=2,
                shared_negative_pixel_count=0,
            ),
            NegativeProvenanceKind.HARD_NEGATIVE,
        ),
        (
            TileNegativeProvenance(
                tile_id="tile",
                ordinary_negative_pixel_count=2,
                hard_negative_pixel_count=2,
                shared_negative_pixel_count=1,
            ),
            NegativeProvenanceKind.MIXED_NEGATIVE,
        ),
    ],
)
def test_negative_provenance_kind_is_source_derived(
    record: TileNegativeProvenance,
    expected_kind: NegativeProvenanceKind,
) -> None:
    assert record.kind == expected_kind


def test_union_negative_count_subtracts_shared_overlap() -> None:
    record = TileNegativeProvenance(
        tile_id="tile",
        ordinary_negative_pixel_count=3,
        hard_negative_pixel_count=2,
        shared_negative_pixel_count=1,
    )
    assert record.union_negative_pixel_count == 4


def test_record_validation_accepts_reconciled_counts() -> None:
    candidate = make_candidate(
        digest_character="c",
        row_index=0,
        negative_pixel_count=3,
    )
    record = TileNegativeProvenance(
        tile_id=candidate.tile_id,
        ordinary_negative_pixel_count=2,
        hard_negative_pixel_count=2,
        shared_negative_pixel_count=1,
    )
    assert validate_tile_negative_provenance(
        record,
        candidate=candidate,
    ) == ()


def test_record_validation_rejects_unexplained_negative_pixels() -> None:
    candidate = make_candidate(
        digest_character="c",
        row_index=0,
        negative_pixel_count=2,
    )
    record = TileNegativeProvenance(
        tile_id=candidate.tile_id,
        ordinary_negative_pixel_count=1,
        hard_negative_pixel_count=0,
        shared_negative_pixel_count=0,
    )
    errors = validate_tile_negative_provenance(
        record,
        candidate=candidate,
    )
    assert (
        "source-derived negative union must match the "
        "candidate negative_pixel_count."
        in errors
    )


def test_record_validation_rejects_impossible_shared_count() -> None:
    candidate = make_candidate(
        digest_character="c",
        row_index=0,
        negative_pixel_count=2,
    )
    record = TileNegativeProvenance(
        tile_id=candidate.tile_id,
        ordinary_negative_pixel_count=1,
        hard_negative_pixel_count=1,
        shared_negative_pixel_count=2,
    )
    errors = validate_tile_negative_provenance(
        record,
        candidate=candidate,
    )
    assert (
        "shared_negative_pixel_count must not exceed "
        "ordinary_negative_pixel_count."
        in errors
    )
    assert (
        "shared_negative_pixel_count must not exceed "
        "hard_negative_pixel_count."
        in errors
    )


def test_provenance_catalog_accepts_complete_ordered_records() -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    assert provenance.record_count == 3
    assert provenance.hard_negative_tile_count == 1
    assert validate_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
    ) == ()


def test_catalog_validation_rejects_incomplete_records() -> None:
    catalog = make_catalog()
    provenance = replace(
        make_provenance_catalog(),
        records=make_provenance_catalog().records[:-1],
    )
    errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
    )
    assert (
        "provenance records must cover the complete catalog "
        "in catalog order."
        in errors
    )


def test_catalog_validation_rejects_wrong_catalog_identity() -> None:
    catalog = make_catalog()
    provenance = replace(
        make_provenance_catalog(),
        tile_catalog_id="sha256:" + ("0" * 64),
    )
    errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
    )
    assert (
        "tile_catalog_id must match the candidate catalog."
        in errors
    )


def test_catalog_validation_rejects_same_source_identity() -> None:
    catalog = make_catalog()
    provenance = replace(
        make_provenance_catalog(),
        hard_negative_source_id="ordinary-negative",
    )
    errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
    )
    assert (
        "ordinary and hard-negative source IDs must differ."
        in errors
    )