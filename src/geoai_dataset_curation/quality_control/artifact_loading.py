"Validated loading of persisted pair-QC input artifacts"
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TILE_SAMPLING_SELECTION_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
    build_image_mask_pair_catalog_id,
    build_tile_negative_provenance_catalog_id,
    build_tile_sampling_selection_id,
    validate_image_mask_pair_catalog,
    validate_tile_negative_provenance_catalog,
    validate_tile_sampling_selection,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
    validate_tile_catalog,
)


@dataclass(frozen=True)
class PairQCInputArtifacts:
    "Persisted upstream artifacts required by pair QC"
    tile_catalog: TileCatalog
    selection: TileSamplingSelection
    provenance: TileNegativeProvenanceCatalog
    pair_catalog: ImageMaskPairCatalog


def _read_json_object(path: Path) -> dict[str, Any]:
    "Read one JSON artifact with an object root"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Artifact is not readable JSON: {path}") from error

    if not isinstance(payload, dict):
        raise ValueError(f"Artifact root must be an object: {path}")

    return payload


def _candidate_from_dict(payload: dict[str, Any]) -> TileCandidateRecord:
    "Deserialize one candidate-tile record"

    return TileCandidateRecord(
        tile_id=str(payload["tile_id"]),
        grid_id=str(payload["grid_id"]),
        layout_id=str(payload["layout_id"]),
        row_index=int(payload["row_index"]),
        column_index=int(payload["column_index"]),
        row_offset_pixels=int(payload["row_offset_pixels"]),
        column_offset_pixels=int(payload["column_offset_pixels"]),
        read_width_pixels=int(payload["read_width_pixels"]),
        read_height_pixels=int(payload["read_height_pixels"]),
        output_width_pixels=int(payload["output_width_pixels"]),
        output_height_pixels=int(payload["output_height_pixels"]),
        left=float(payload["left"]),
        bottom=float(payload["bottom"]),
        right=float(payload["right"]),
        top=float(payload["top"]),
        positive_pixel_count=int(payload["positive_pixel_count"]),
        negative_pixel_count=int(payload["negative_pixel_count"]),
        ignore_pixel_count=int(payload["ignore_pixel_count"]),
    )


def load_tile_catalog_artifact(path: Path) -> TileCatalog:
    "Load and verify one persisted candidate-tile catalog"
    payload = _read_json_object(path)

    try:
        catalog = TileCatalog(
            schema_version=str(payload["schema_version"]),
            output_name=str(payload["output_name"]),
            image_artifact_path=str(payload["image_artifact_path"]),
            label_artifact_path=str(payload["label_artifact_path"]),
            grid_id=str(payload["grid_id"]),
            layout_id=str(payload["layout_id"]),
            tiles=tuple(_candidate_from_dict(item) for item in payload["tiles"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid tile catalog artifact: {path}") from error

    if catalog.schema_version != TILE_CATALOG_SCHEMA_VERSION:
        raise ValueError("Tile catalog schema_version is not supported.")

    errors = validate_tile_catalog(catalog)
    if errors:
        message = "Tile catalog artifact is invalid: " + "; ".join(errors)
        raise ValueError(message)

    if payload.get("catalog_id") != build_tile_catalog_id(catalog):
        raise ValueError("Tile catalog artifact identity does not match its content.")

    return catalog


def load_sampling_selection_artifact(
    path: Path,
    *,
    tile_catalog: TileCatalog,
) -> TileSamplingSelection:
    "Load and verify one persisted sampling selection"

    payload = _read_json_object(path)

    if payload.get("schema_version") != TILE_SAMPLING_SELECTION_SCHEMA_VERSION:
        raise ValueError("Sampling selection schema_version is not supported.")

    try:
        selection = TileSamplingSelection(
            catalog_id=str(payload["tile_catalog_id"]),
            selected_candidates=tuple(_candidate_from_dict(item) for item in payload["selected_tiles"]),
            excluded_tile_ids=tuple(str(value) for value in payload["excluded_tile_ids"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid sampling selection artifact: {path}") from error

    errors = validate_tile_sampling_selection(selection, catalog=tile_catalog)
    if errors:
        message = "Sampling selection artifact is invalid: " + "; ".join(errors)
        raise ValueError(message)

    expected_id = build_tile_sampling_selection_id(selection, catalog=tile_catalog)
    if payload.get("selection_id") != expected_id:
        raise ValueError("Sampling selection artifact identity does not match its content.")

    return selection


def load_negative_provenance_artifact(
    path: Path,
    *,
    tile_catalog: TileCatalog,
) -> TileNegativeProvenanceCatalog:
    "Load and verify one persisted negative-provenance catalog"
    payload = _read_json_object(path)

    try:
        provenance = TileNegativeProvenanceCatalog(
            schema_version=str(payload["schema_version"]),
            tile_catalog_id=str(payload["tile_catalog_id"]),
            ordinary_negative_source_id=str(payload["ordinary_negative_source_id"]),
            hard_negative_source_id=str(payload["hard_negative_source_id"]),
            records=tuple(
                TileNegativeProvenance(
                    tile_id=str(item["tile_id"]),
                    ordinary_negative_pixel_count=int(item["ordinary_negative_pixel_count"]),
                    hard_negative_pixel_count=int(item["hard_negative_pixel_count"]),
                    shared_negative_pixel_count=int(item["shared_negative_pixel_count"]),
                )
                for item in payload["records"]
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid negative-provenance artifact: {path}") from error

    if provenance.schema_version != TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION:
        raise ValueError("Negative-provenance schema_version is not supported.")

    errors = validate_tile_negative_provenance_catalog(provenance, catalog=tile_catalog)
    if errors:
        message = "Negative-provenance artifact is invalid: " + "; ".join(errors)
        raise ValueError(message)

    expected_id = build_tile_negative_provenance_catalog_id(provenance, catalog=tile_catalog)
    if payload.get("provenance_catalog_id") != expected_id:
        raise ValueError("Negative-provenance artifact identity does not match its content.")

    return provenance


def load_pair_catalog_artifact(
    path: Path,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
) -> ImageMaskPairCatalog:
    "Load and verify one persisted image-mask pair catalog"
    payload = _read_json_object(path)

    try:
        pair_catalog = ImageMaskPairCatalog(
            schema_version=str(payload["schema_version"]),
            output_name=str(payload["output_name"]),
            tile_catalog_id=str(payload["tile_catalog_id"]),
            selection_id=str(payload["selection_id"]),
            provenance_catalog_id=str(payload["provenance_catalog_id"]),
            source_image_artifact_path=str(payload["source_image_artifact_path"]),
            source_label_artifact_path=str(payload["source_label_artifact_path"]),
            pairs=tuple(
                ImageMaskPairRecord(
                    pair_id=str(item["pair_id"]),
                    tile_id=str(item["tile_id"]),
                    image_tile_path=str(item["image_tile_path"]),
                    mask_tile_path=str(item["mask_tile_path"]),
                    label_class=TileLabelClass(str(item["label_class"])),
                    negative_provenance_kind=NegativeProvenanceKind(str(item["negative_provenance_kind"])),
                )
                for item in payload["pairs"]
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid pair catalog artifact: {path}") from error

    if pair_catalog.schema_version != IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION:
        raise ValueError("Pair catalog schema_version is not supported.")

    errors = validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    if errors:
        message = "Pair catalog artifact is invalid: " + "; ".join(errors)
        raise ValueError(message)

    if payload.get("pair_catalog_id") != build_image_mask_pair_catalog_id(pair_catalog):
        raise ValueError("Pair catalog artifact identity does not match its content.")

    return pair_catalog


def load_pair_qc_input_artifacts(
    *,
    tile_catalog_path: Path,
    selection_path: Path,
    provenance_path: Path,
    pair_catalog_path: Path,
) -> PairQCInputArtifacts:
    "Load and cross-validate every persisted pair-QC input"
    tile_catalog = load_tile_catalog_artifact(tile_catalog_path)
    selection = load_sampling_selection_artifact(selection_path, tile_catalog=tile_catalog)
    provenance = load_negative_provenance_artifact(provenance_path, tile_catalog=tile_catalog)
    pair_catalog = load_pair_catalog_artifact(
        pair_catalog_path,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )

    return PairQCInputArtifacts(
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        pair_catalog=pair_catalog,
    )