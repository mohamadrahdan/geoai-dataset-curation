"Serialization and persistence for candidate tile catalogs"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
    tile_candidate_identity_payload,
    tile_catalog_identity_payload,
)


def tile_candidate_record_to_dict(
    record: TileCandidateRecord,
) -> dict[str, Any]:
    "Serialize one candidate tile record"
    payload = tile_candidate_identity_payload(record)
    payload.update(
        {
            "label_class": record.label_class.value,
            "output_pixel_count": record.output_pixel_count,
            "read_pixel_count": record.read_pixel_count,
            "padding_pixel_count": record.padding_pixel_count,
            "supervised_pixel_count": record.supervised_pixel_count,
        }
    )
    return payload


def tile_catalog_to_dict(catalog: TileCatalog) -> dict[str, Any]:
    "Serialize one validated candidate tile catalog"
    errors = validate_tile_catalog(catalog)
    if errors:
        raise ValueError(
            "Cannot serialize invalid tile catalog: " + "; ".join(errors)
        )
    identity_payload = tile_catalog_identity_payload(catalog)

    return {
        "catalog_id": build_tile_catalog_id(catalog),
        "schema_version": identity_payload["schema_version"],
        "output_name": identity_payload["output_name"],
        "image_artifact_path": identity_payload["image_artifact_path"],
        "label_artifact_path": identity_payload["label_artifact_path"],
        "grid_id": identity_payload["grid_id"],
        "layout_id": identity_payload["layout_id"],
        "tile_count": catalog.tile_count,
        "tiles": [
            tile_candidate_record_to_dict(record)
            for record in catalog.tiles
        ],
    }


def write_tile_catalog(catalog: TileCatalog, output_path: Path) -> Path:
    "Write one candidate tile catalog as canonical formatted JSON"
    payload = tile_catalog_to_dict(catalog)
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


def verify_tile_catalog_artifact(
    catalog: TileCatalog,
    artifact_path: Path,
) -> tuple[str, ...]:
    "Verify a persisted catalog against its expected in-memory value"
    if not artifact_path.is_file():
        return ("catalog artifact does not exist.",)
    try:
        observed = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("catalog artifact must contain valid UTF-8 JSON.",)
    expected = tile_catalog_to_dict(catalog)
    if observed != expected:
        return ("catalog artifact content does not match expected catalog.",)

    return ()