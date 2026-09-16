from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    build_tile_negative_provenance_catalog_id,
    tile_negative_provenance_catalog_identity_payload,
    tile_negative_provenance_identity_payload,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
TILE_ID = "sha256:" + ("c" * 64)


def make_catalog() -> TileCatalog:
    candidate = TileCandidateRecord(
        tile_id=TILE_ID,
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=2,
        read_height_pixels=2,
        output_width_pixels=2,
        output_height_pixels=2,
        left=0.0,
        bottom=0.0,
        right=20.0,
        top=20.0,
        positive_pixel_count=0,
        negative_pixel_count=3,
        ignore_pixel_count=1,
    )
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="negative-provenance-candidates",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(candidate,),
    )


def make_provenance_catalog() -> TileNegativeProvenanceCatalog:
    catalog = make_catalog()
    return TileNegativeProvenanceCatalog(
        schema_version=TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        tile_catalog_id=build_tile_catalog_id(catalog),
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        records=(
            TileNegativeProvenance(
                tile_id=TILE_ID,
                ordinary_negative_pixel_count=2,
                hard_negative_pixel_count=2,
                shared_negative_pixel_count=1,
            ),
        ),
    )


def test_record_identity_payload_contains_stored_fields() -> None:
    record = make_provenance_catalog().records[0]
    assert tile_negative_provenance_identity_payload(record) == {
        "tile_id": TILE_ID,
        "ordinary_negative_pixel_count": 2,
        "hard_negative_pixel_count": 2,
        "shared_negative_pixel_count": 1,
    }


def test_catalog_identity_payload_preserves_ordered_evidence() -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    payload = tile_negative_provenance_catalog_identity_payload(
        provenance,
        catalog=catalog,
    )
    assert payload == {
        "schema_version": TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        "tile_catalog_id": build_tile_catalog_id(catalog),
        "ordinary_negative_source_id": "ordinary-negative",
        "hard_negative_source_id": "hard-negative",
        "records": [
            {
                "tile_id": TILE_ID,
                "ordinary_negative_pixel_count": 2,
                "hard_negative_pixel_count": 2,
                "shared_negative_pixel_count": 1,
            }
        ],
    }


def test_provenance_catalog_identity_is_stable() -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    first_id = build_tile_negative_provenance_catalog_id(
        provenance,
        catalog=catalog,
    )
    second_id = build_tile_negative_provenance_catalog_id(
        provenance,
        catalog=catalog,
    )
    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_source_identity_changes_provenance_identity() -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    changed = replace(
        provenance,
        ordinary_negative_source_id="ordinary-negative-v2",
    )
    original_id = build_tile_negative_provenance_catalog_id(
        provenance,
        catalog=catalog,
    )
    changed_id = build_tile_negative_provenance_catalog_id(
        changed,
        catalog=catalog,
    )
    assert original_id != changed_id


def test_identity_rejects_invalid_provenance_catalog() -> None:
    catalog = make_catalog()
    provenance = replace(make_provenance_catalog(), records=(),)
    with pytest.raises(
        ValueError,
        match="Cannot identify invalid tile negative provenance",
    ):
        build_tile_negative_provenance_catalog_id(
            provenance,
            catalog=catalog,
        )