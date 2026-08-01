"Stable identity helpers for exact raster grids"

import hashlib
import json
from typing import Any
from geoai_dataset_curation.image_construction.contracts import (RasterGridSpec)


def raster_grid_identity_payload(
    grid: RasterGridSpec,
) -> dict[str, Any]:
    "Return the canonical identity payload for one raster grid"

    transform = grid.transform

    return {
        "schema_version": "raster-grid-v1",
        "crs": grid.crs,
        "width": grid.width,
        "height": grid.height,
        "pixel_size_x": grid.pixel_size_x,
        "pixel_size_y": grid.pixel_size_y,
        "transform": (
            list(transform.as_tuple)
            if transform is not None
            else None
        ),
    }


def build_raster_grid_id(grid: RasterGridSpec) -> str:
    "Build a stable SHA-256 identifier from the complete grid definition"

    payload = raster_grid_identity_payload(grid)
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


def raster_grids_match(
    left: RasterGridSpec,
    right: RasterGridSpec,
) -> bool:
    "Return whether two raster grids have the same exact identity"

    return build_raster_grid_id(left) == build_raster_grid_id(right)