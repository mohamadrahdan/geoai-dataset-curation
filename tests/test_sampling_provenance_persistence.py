import json
from pathlib import Path
import pytest
from geoai_dataset_curation.sampling import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    build_tile_negative_provenance_catalog_id,
    tile_negative_provenance_catalog_to_dict,
    tile_negative_provenance_to_dict,
    verify_tile_negative_provenance_artifact,
    write_tile_negative_provenance_catalog,
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


def test_record_serialization_includes_derived_fields() -> None:
    record = make_provenance_catalog().records[0]
    assert tile_negative_provenance_to_dict(record) == {
        "tile_id": TILE_ID,
        "ordinary_negative_pixel_count": 2,
        "hard_negative_pixel_count": 2,
        "shared_negative_pixel_count": 1,
        "union_negative_pixel_count": 3,
        "kind": "mixed_negative",
    }


def test_catalog_serialization_includes_identity_and_summary() -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    payload = tile_negative_provenance_catalog_to_dict(
        provenance,
        catalog=catalog,
    )
    assert payload["provenance_catalog_id"] == (
        build_tile_negative_provenance_catalog_id(
            provenance,
            catalog=catalog,
        )
    )
    assert payload["schema_version"] == (TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION)
    assert payload["tile_catalog_id"] == build_tile_catalog_id(catalog)
    assert payload["ordinary_negative_source_id"] == "ordinary-negative"
    assert payload["hard_negative_source_id"] == "hard-negative"
    assert payload["record_count"] == 1
    assert payload["hard_negative_tile_count"] == 1
    assert payload["records"] == [
        tile_negative_provenance_to_dict(
            provenance.records[0]
        )
    ]


def test_writer_creates_canonical_json_artifact(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    output_path = tmp_path / "nested" / "provenance.json"
    result = write_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
        output_path=output_path,
    )
    assert result == output_path
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(
        output_path.read_text(encoding="utf-8")
    ) == tile_negative_provenance_catalog_to_dict(
        provenance,
        catalog=catalog,
    )


def test_verification_accepts_matching_artifact(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    output_path = tmp_path / "provenance.json"
    write_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
        output_path=output_path,
    )
    assert verify_tile_negative_provenance_artifact(
        provenance,
        catalog=catalog,
        artifact_path=output_path,
    ) == ()


def test_verification_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    errors = verify_tile_negative_provenance_artifact(
        make_provenance_catalog(),
        catalog=make_catalog(),
        artifact_path=tmp_path / "missing.json",
    )
    assert errors == ("provenance artifact does not exist.",)


def test_verification_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "provenance.json"
    artifact_path.write_text(
        "{invalid-json",
        encoding="utf-8",
    )

    errors = verify_tile_negative_provenance_artifact(
        make_provenance_catalog(),
        catalog=make_catalog(),
        artifact_path=artifact_path,
    )

    assert errors == ("provenance artifact must contain valid UTF-8 JSON.",)


def test_verification_rejects_changed_content(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    provenance = make_provenance_catalog()
    artifact_path = tmp_path / "provenance.json"
    write_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
        output_path=artifact_path,
    )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["record_count"] = 99
    artifact_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    errors = verify_tile_negative_provenance_artifact(
        provenance,
        catalog=catalog,
        artifact_path=artifact_path,
    )
    assert errors == ("provenance artifact content does not match expected provenance.",)


def test_serialization_rejects_invalid_provenance() -> None:
    catalog = make_catalog()
    provenance = TileNegativeProvenanceCatalog(
        schema_version=TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        tile_catalog_id=build_tile_catalog_id(catalog),
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        records=(),
    )

    with pytest.raises(
        ValueError,
        match="Cannot identify invalid tile negative provenance",):
        tile_negative_provenance_catalog_to_dict(
            provenance,
            catalog=catalog,
        )