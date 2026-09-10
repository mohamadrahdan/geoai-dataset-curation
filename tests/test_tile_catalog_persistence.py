from dataclasses import replace
import json
from pathlib import Path
import pytest
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    build_tile_catalog_id,
    tile_catalog_to_dict,
    verify_tile_catalog_artifact,
    write_tile_catalog,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
TILE_ID = "sha256:" + ("c" * 64)


def make_record() -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id=TILE_ID,
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=100.0,
        bottom=160.0,
        right=140.0,
        top=200.0,
        positive_pixel_count=1,
        negative_pixel_count=2,
        ignore_pixel_count=13,
    )


def make_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="loop1_candidate_tiles",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(make_record(),),
    )


def test_tile_catalog_identity_is_stable_and_content_sensitive() -> None:
    catalog = make_catalog()
    changed_record = replace(
        catalog.tiles[0],
        positive_pixel_count=2,
        ignore_pixel_count=12,
    )
    changed_catalog = replace(catalog, tiles=(changed_record,))
    assert build_tile_catalog_id(catalog) == build_tile_catalog_id(catalog)
    assert build_tile_catalog_id(catalog) != build_tile_catalog_id(
        changed_catalog
    )


def test_tile_catalog_serialization_includes_identity_and_derived_fields() -> None:
    catalog = make_catalog()
    payload = tile_catalog_to_dict(catalog)
    assert payload["catalog_id"] == build_tile_catalog_id(catalog)
    assert payload["tile_count"] == 1
    assert payload["tiles"][0]["label_class"] == "positive"
    assert payload["tiles"][0]["supervised_pixel_count"] == 3
    assert payload["tiles"][0]["padding_pixel_count"] == 0


def test_write_and_verify_tile_catalog(tmp_path: Path) -> None:
    catalog = make_catalog()
    output_path = tmp_path / "tiles.catalog.json"
    written_path = write_tile_catalog(catalog, output_path)
    errors = verify_tile_catalog_artifact(catalog, written_path)
    assert written_path == output_path
    assert written_path.read_text(encoding="utf-8").endswith("\n")
    assert errors == ()


def test_verify_tile_catalog_detects_modified_artifact(tmp_path: Path) -> None:
    catalog = make_catalog()
    output_path = write_tile_catalog(
        catalog,
        tmp_path / "tiles.catalog.json",
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    payload["tile_count"] = 999
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    errors = verify_tile_catalog_artifact(catalog, output_path)
    assert errors == (
        "catalog artifact content does not match expected catalog.",
    )


def test_tile_catalog_serialization_rejects_invalid_catalog() -> None:
    catalog = replace(make_catalog(), schema_version="unsupported")
    with pytest.raises(ValueError, match="invalid tile catalog"):
        tile_catalog_to_dict(catalog)