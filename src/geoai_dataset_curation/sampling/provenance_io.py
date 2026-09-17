"Serialization and persistence for tile negative provenance"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
)
from geoai_dataset_curation.sampling.provenance_identity import (
    build_tile_negative_provenance_catalog_id,
    tile_negative_provenance_catalog_identity_payload,
)
from geoai_dataset_curation.tiling.catalog import TileCatalog


def tile_negative_provenance_to_dict(
    record: TileNegativeProvenance,
) -> dict[str, Any]:
    "Serialize one tile negative provenance record"
    return {
        "tile_id": record.tile_id,
        "ordinary_negative_pixel_count": record.ordinary_negative_pixel_count,
        "hard_negative_pixel_count": record.hard_negative_pixel_count,
        "shared_negative_pixel_count": record.shared_negative_pixel_count,
        "union_negative_pixel_count": record.union_negative_pixel_count,
        "kind": record.kind.value,
    }


def tile_negative_provenance_catalog_to_dict(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
) -> dict[str, Any]:
    "Serialize one validated tile negative provenance catalog"
    identity_payload = tile_negative_provenance_catalog_identity_payload(
        provenance,
        catalog=catalog,
    )
    return {
        "provenance_catalog_id": build_tile_negative_provenance_catalog_id(
            provenance,
            catalog=catalog,
        ),
        "schema_version": identity_payload["schema_version"],
        "tile_catalog_id": identity_payload["tile_catalog_id"],
        "ordinary_negative_source_id": identity_payload[
            "ordinary_negative_source_id"
        ],
        "hard_negative_source_id": identity_payload[
            "hard_negative_source_id"
        ],
        "record_count": provenance.record_count,
        "hard_negative_tile_count": provenance.hard_negative_tile_count,
        "records": [
            tile_negative_provenance_to_dict(record)
            for record in provenance.records
        ],
    }


def write_tile_negative_provenance_catalog(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
    output_path: Path,
) -> Path:
    "Write one tile negative provenance catalog as canonical JSON"
    payload = tile_negative_provenance_catalog_to_dict(
        provenance,
        catalog=catalog,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output_path


def verify_tile_negative_provenance_artifact(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
    artifact_path: Path,
) -> tuple[str, ...]:
    "Verify a persisted provenance artifact against its expected value"
    if not artifact_path.is_file():
        return ("provenance artifact does not exist.",)
    try:
        observed = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("provenance artifact must contain valid UTF-8 JSON.",)
    expected = tile_negative_provenance_catalog_to_dict(
        provenance,
        catalog=catalog,
    )
    if observed != expected:
        return (
            "provenance artifact content does not match "
            "expected provenance.",
        )
    return ()