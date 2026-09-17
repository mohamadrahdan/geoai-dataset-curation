"Serialization and persistence for image-mask pair catalogs"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.pair_identity import (
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.sampling.pair_validation import (
    validate_image_mask_pair_catalog,
)
from geoai_dataset_curation.tiling.catalog import TileCatalog


def image_mask_pair_record_to_dict(
    pair: ImageMaskPairRecord,
) -> dict[str, Any]:
    "Serialize one image-mask pair record"
    return {
        "pair_id": pair.pair_id,
        "tile_id": pair.tile_id,
        "image_tile_path": pair.image_tile_path,
        "mask_tile_path": pair.mask_tile_path,
        "label_class": pair.label_class.value,
        "negative_provenance_kind": (
            pair.negative_provenance_kind.value
        ),
    }


def image_mask_pair_catalog_to_dict(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
) -> dict[str, Any]:
    "Serialize one validated image-mask pair catalog"
    errors = validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    if errors:
        raise ValueError(
            "Cannot serialize invalid image-mask pair catalog: "
            + "; ".join(errors)
        )

    return {
        "pair_catalog_id": build_image_mask_pair_catalog_id(
            pair_catalog
        ),
        "schema_version": pair_catalog.schema_version,
        "output_name": pair_catalog.output_name,
        "tile_catalog_id": pair_catalog.tile_catalog_id,
        "selection_id": pair_catalog.selection_id,
        "provenance_catalog_id": (
            pair_catalog.provenance_catalog_id
        ),
        "source_image_artifact_path": (
            pair_catalog.source_image_artifact_path
        ),
        "source_label_artifact_path": (
            pair_catalog.source_label_artifact_path
        ),
        "pair_count": pair_catalog.pair_count,
        "positive_pair_count": pair_catalog.positive_pair_count,
        "negative_only_pair_count": (
            pair_catalog.negative_only_pair_count
        ),
        "pairs": [
            image_mask_pair_record_to_dict(pair)
            for pair in pair_catalog.pairs
        ],
    }


def write_image_mask_pair_catalog(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
    output_path: Path,
) -> Path:
    "Write one image-mask pair catalog as canonical JSON"
    payload = image_mask_pair_catalog_to_dict(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
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


def verify_image_mask_pair_catalog_artifact(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
    artifact_path: Path,
) -> tuple[str, ...]:
    "Verify a persisted pair catalog against its expected value"
    if not artifact_path.is_file():
        return ("pair catalog artifact does not exist.",)
    try:
        observed = json.loads(
            artifact_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("pair catalog artifact must contain valid UTF-8 JSON.",)
    expected = image_mask_pair_catalog_to_dict(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    if observed != expected:
        return (
            "pair catalog artifact content does not match "
            "expected pair catalog.",
        )
    return ()