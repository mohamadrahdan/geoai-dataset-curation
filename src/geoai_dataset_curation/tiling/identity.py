"Stable identity helpers for tile layouts and windows"
import hashlib
import json
from typing import Any
from geoai_dataset_curation.tiling.contracts import (
    TileLayoutSpec,
)


def _build_sha256_id(
    payload: dict[str, Any],
) -> str:
    "Build a stable SHA-256 identifier from a canonical payload"
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    digest = hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def tile_layout_identity_payload(
    layout: TileLayoutSpec,
) -> dict[str, Any]:
    "Return the canonical identity payload for one tile layout"
    return {
        "schema_version": "tile-layout-v1",
        "tile_width_pixels": layout.tile_width_pixels,
        "tile_height_pixels": layout.tile_height_pixels,
        "stride_x_pixels": layout.stride_x_pixels,
        "stride_y_pixels": layout.stride_y_pixels,
        "edge_policy": layout.edge_policy.value,
    }


def build_tile_layout_id(
    layout: TileLayoutSpec,
) -> str:
    "Build a stable identifier for one complete tile layout"
    return _build_sha256_id(
        tile_layout_identity_payload(layout)
    )


def tile_window_identity_payload(
    *,
    grid_id: str,
    layout: TileLayoutSpec,
    row_index: int,
    column_index: int,
    row_offset_pixels: int,
    column_offset_pixels: int,
    read_width_pixels: int,
    read_height_pixels: int,
) -> dict[str, Any]:
    "Return the canonical identity payload for one tile window"
    return {
        "schema_version": "tile-window-v1",
        "grid_id": grid_id,
        "layout_id": build_tile_layout_id(layout),
        "row_index": row_index,
        "column_index": column_index,
        "row_offset_pixels": row_offset_pixels,
        "column_offset_pixels": column_offset_pixels,
        "read_width_pixels": read_width_pixels,
        "read_height_pixels": read_height_pixels,
    }


def build_tile_window_id(
    *,
    grid_id: str,
    layout: TileLayoutSpec,
    row_index: int,
    column_index: int,
    row_offset_pixels: int,
    column_offset_pixels: int,
    read_width_pixels: int,
    read_height_pixels: int,
) -> str:
    "Build a stable identifier for one exact tile window"
    payload = tile_window_identity_payload(
        grid_id=grid_id,
        layout=layout,
        row_index=row_index,
        column_index=column_index,
        row_offset_pixels=row_offset_pixels,
        column_offset_pixels=column_offset_pixels,
        read_width_pixels=read_width_pixels,
        read_height_pixels=read_height_pixels,
    )
    return _build_sha256_id(payload)