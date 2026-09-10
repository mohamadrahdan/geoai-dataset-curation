from dataclasses import replace
import pytest
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    validate_tile_candidate_record,
    validate_tile_catalog,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)


def make_record(
    *,
    tile_character: str = "c",
    row_index: int = 0,
    column_index: int = 0,
    positive_pixel_count: int = 1,
    negative_pixel_count: int = 2,
    ignore_pixel_count: int = 13,
) -> TileCandidateRecord:
    left = float(column_index * 40)
    top = float(1000 - row_index * 40)

    return TileCandidateRecord(
        tile_id="sha256:" + (tile_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=column_index,
        row_offset_pixels=row_index * 4,
        column_offset_pixels=column_index * 4,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=left,
        bottom=top - 40.0,
        right=left + 40.0,
        top=top,
        positive_pixel_count=positive_pixel_count,
        negative_pixel_count=negative_pixel_count,
        ignore_pixel_count=ignore_pixel_count,
    )


def make_catalog(
    tiles: tuple[TileCandidateRecord, ...] | None = None,
) -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="loop1_candidate_tiles",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=tiles if tiles is not None else (make_record(),),
    )


@pytest.mark.parametrize(
    ("positive_count", "negative_count", "expected_class"),
    [
        (1, 0, TileLabelClass.POSITIVE),
        (0, 1, TileLabelClass.NEGATIVE_ONLY),
        (0, 0, TileLabelClass.ALL_IGNORE),
    ],
)
def test_tile_candidate_derives_label_class(
    positive_count: int,
    negative_count: int,
    expected_class: TileLabelClass,
) -> None:
    record = make_record(
        positive_pixel_count=positive_count,
        negative_pixel_count=negative_count,
        ignore_pixel_count=16 - positive_count - negative_count,
    )
    assert record.label_class == expected_class
    assert record.supervised_pixel_count == positive_count + negative_count


def test_validate_tile_catalog_accepts_valid_catalog() -> None:
    catalog = make_catalog()
    assert catalog.tile_count == 1
    assert validate_tile_candidate_record(catalog.tiles[0]) == ()
    assert validate_tile_catalog(catalog) == ()


def test_validate_tile_candidate_rejects_inconsistent_label_counts() -> None:
    record = replace(make_record(), ignore_pixel_count=12)
    errors = validate_tile_candidate_record(record)
    assert "label pixel counts must equal the output pixel count." in errors


def test_validate_tile_catalog_rejects_duplicate_tile_ids() -> None:
    first = make_record(column_index=0)
    second = make_record(column_index=1)
    errors = validate_tile_catalog(make_catalog((first, second)))
    assert "tile_id values must be unique." in errors


def test_validate_tile_catalog_rejects_non_row_major_order() -> None:
    first = make_record(tile_character="c", column_index=1)
    second = make_record(tile_character="d", column_index=0)
    errors = validate_tile_catalog(make_catalog((first, second)))
    assert "tiles must use deterministic row-major ordering." in errors


def test_validate_tile_catalog_rejects_grid_mismatch() -> None:
    record = replace(make_record(), grid_id="sha256:" + ("d" * 64))
    errors = validate_tile_catalog(make_catalog((record,)))
    assert "tiles[0]: grid_id must match the catalog grid_id." in errors


def test_validate_tile_candidate_rejects_invalid_bounds() -> None:
    record = replace(make_record(), right=0.0)
    errors = validate_tile_candidate_record(record)
    assert "left must be smaller than right." in errors