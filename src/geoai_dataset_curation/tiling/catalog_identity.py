"Stable identity helpers for candidate tile catalogs"
from typing import Any
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.identity import _build_sha256_id


def tile_candidate_identity_payload(
    record: TileCandidateRecord,
) -> dict[str, Any]:
    "Return the canonical identity payload for one candidate tile"
    return {
        "tile_id": record.tile_id,
        "grid_id": record.grid_id,
        "layout_id": record.layout_id,
        "row_index": record.row_index,
        "column_index": record.column_index,
        "row_offset_pixels": record.row_offset_pixels,
        "column_offset_pixels": record.column_offset_pixels,
        "read_width_pixels": record.read_width_pixels,
        "read_height_pixels": record.read_height_pixels,
        "output_width_pixels": record.output_width_pixels,
        "output_height_pixels": record.output_height_pixels,
        "left": record.left,
        "bottom": record.bottom,
        "right": record.right,
        "top": record.top,
        "positive_pixel_count": record.positive_pixel_count,
        "negative_pixel_count": record.negative_pixel_count,
        "ignore_pixel_count": record.ignore_pixel_count,
    }


def tile_catalog_identity_payload(catalog: TileCatalog) -> dict[str, Any]:
    "Return the canonical identity payload for one candidate catalog"
    errors = validate_tile_catalog(catalog)
    if errors:
        raise ValueError(
            "Cannot identify invalid tile catalog: " + "; ".join(errors)
        )
    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "image_artifact_path": catalog.image_artifact_path,
        "label_artifact_path": catalog.label_artifact_path,
        "grid_id": catalog.grid_id,
        "layout_id": catalog.layout_id,
        "tiles": [
            tile_candidate_identity_payload(record)
            for record in catalog.tiles
        ],
    }


def build_tile_catalog_id(catalog: TileCatalog) -> str:
    "Build a stable identifier for one complete candidate catalog"
    return _build_sha256_id(tile_catalog_identity_payload(catalog))