"Deterministic construction of candidate tile catalogs"
from affine import Affine
import numpy as np
from rasterio.windows import Window, bounds
from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.tiling.catalog import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.contracts import (
    TileWindowSpec,
    TilingRequest,
)
from geoai_dataset_curation.tiling.identity import build_tile_layout_id
from geoai_dataset_curation.tiling.label_analysis import validate_label_array
from geoai_dataset_curation.tiling.validation import validate_tiling_request
from geoai_dataset_curation.tiling.window_generation import generate_tile_windows


def _window_bounds(
    window: TileWindowSpec,
    transform: Affine,
) -> tuple[float, float, float, float]:
    raster_window = Window.from_slices(
        rows=(
            window.row_offset_pixels,
            window.row_offset_pixels + window.read_height_pixels,
        ),
        cols=(
            window.column_offset_pixels,
            window.column_offset_pixels + window.read_width_pixels,
        ),
    )
    left, bottom, right, top = bounds(raster_window, transform)
    return float(left), float(bottom), float(right), float(top)


def _build_candidate_record(
    *,
    labels: np.ndarray,
    window: TileWindowSpec,
    grid_id: str,
    layout_id: str,
    transform: Affine,
) -> TileCandidateRecord:
    row_start = window.row_offset_pixels
    row_end = row_start + window.read_height_pixels
    column_start = window.column_offset_pixels
    column_end = column_start + window.read_width_pixels

    tile_labels = labels[row_start:row_end, column_start:column_end]

    positive_count = int(
        np.count_nonzero(tile_labels == int(LabelValue.POSITIVE))
    )
    negative_count = int(
        np.count_nonzero(tile_labels == int(LabelValue.NEGATIVE))
    )
    source_ignore_count = int(
        np.count_nonzero(tile_labels == int(LabelValue.IGNORE))
    )
    output_pixel_count = (
        window.output_width_pixels * window.output_height_pixels
    )
    read_pixel_count = window.read_width_pixels * window.read_height_pixels
    padded_ignore_count = output_pixel_count - read_pixel_count
    left, bottom, right, top = _window_bounds(window, transform)

    return TileCandidateRecord(
        tile_id=window.tile_id,
        grid_id=grid_id,
        layout_id=layout_id,
        row_index=window.row_index,
        column_index=window.column_index,
        row_offset_pixels=window.row_offset_pixels,
        column_offset_pixels=window.column_offset_pixels,
        read_width_pixels=window.read_width_pixels,
        read_height_pixels=window.read_height_pixels,
        output_width_pixels=window.output_width_pixels,
        output_height_pixels=window.output_height_pixels,
        left=left,
        bottom=bottom,
        right=right,
        top=top,
        positive_pixel_count=positive_count,
        negative_pixel_count=negative_count,
        ignore_pixel_count=source_ignore_count + padded_ignore_count,
    )


def build_tile_catalog(
    labels: np.ndarray,
    request: TilingRequest,
) -> TileCatalog:
    "Build a validated candidate catalog from one aligned label array"
    request_errors = validate_tiling_request(request)
    if request_errors:
        raise ValueError(
            "Cannot build tile catalog: " + "; ".join(request_errors)
        )
    validate_label_array(labels, request)

    transform_spec = request.grid.transform
    if transform_spec is None:
        raise ValueError("Cannot build tile catalog without an exact transform.")
    transform = Affine(*transform_spec.as_tuple)
    layout_id = build_tile_layout_id(request.layout)
    windows = generate_tile_windows(request)
    tiles = tuple(
        _build_candidate_record(
            labels=labels,
            window=window,
            grid_id=request.grid_id,
            layout_id=layout_id,
            transform=transform,
        )
        for window in windows
    )

    catalog = TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name=request.output_name,
        image_artifact_path=request.image_artifact_path.as_posix(),
        label_artifact_path=request.label_artifact_path.as_posix(),
        grid_id=request.grid_id,
        layout_id=layout_id,
        tiles=tiles,
    )

    catalog_errors = validate_tile_catalog(catalog)
    if catalog_errors:
        raise ValueError(
            "Cannot build invalid tile catalog: " + "; ".join(catalog_errors)
        )

    return catalog