"Validation rules for deterministic raster-tiling requests"
from geoai_dataset_curation.image_construction.contracts import (
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.validation import (
    validate_exact_raster_grid_spec,
)
from geoai_dataset_curation.tiling.contracts import (
    TileEdgePolicy,
    TileLayoutSpec,
    TileWindowSpec,
    TilingRequest,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling.identity import (
    build_tile_window_id,
)


def validate_tile_layout(
    layout: TileLayoutSpec,
) -> tuple[str, ...]:
    "Return validation errors for one candidate tile layout"
    errors: list[str] = []
    if not isinstance(
        layout.edge_policy,
        TileEdgePolicy,
    ):
        errors.append(
            "edge_policy must be a TileEdgePolicy."
        )
    if layout.tile_width_pixels <= 0:
        errors.append("tile_width_pixels must be greater than zero.")
    if layout.tile_height_pixels <= 0:
        errors.append("tile_height_pixels must be greater than zero.")
    if layout.stride_x_pixels <= 0:
        errors.append("stride_x_pixels must be greater than zero.")
    if layout.stride_y_pixels <= 0:
        errors.append("stride_y_pixels must be greater than zero.")
    if (
        layout.tile_width_pixels > 0
        and layout.stride_x_pixels
        > layout.tile_width_pixels
    ):
        errors.append(
            "stride_x_pixels must not exceed "
            "tile_width_pixels."
        )
    if (
        layout.tile_height_pixels > 0
        and layout.stride_y_pixels
        > layout.tile_height_pixels
    ):
        errors.append(
            "stride_y_pixels must not exceed "
            "tile_height_pixels."
        )

    return tuple(errors)


def validate_tile_window(
    window: TileWindowSpec,
    *,
    grid: RasterGridSpec,
    layout: TileLayoutSpec,
) -> tuple[str, ...]:
    "Return validation errors for one candidate tile window"
    errors: list[str] = []
    if not window.tile_id.strip():
        errors.append("tile_id must not be empty.")
    if window.row_index < 0:
        errors.append("row_index must be greater than or equal to zero.")
    if window.column_index < 0:
        errors.append("column_index must be greater than or equal to zero.")
    if window.row_offset_pixels < 0:
        errors.append("row_offset_pixels must be greater than or equal to zero.")
    if window.column_offset_pixels < 0:
        errors.append("column_offset_pixels must be greater than or equal to zero.")
    if window.read_width_pixels <= 0:
        errors.append("read_width_pixels must be greater than zero.")
    if window.read_height_pixels <= 0:
        errors.append("read_height_pixels must be greater than zero.")
    if window.output_width_pixels <= 0:
        errors.append("output_width_pixels must be greater than zero.")
    if window.output_height_pixels <= 0:
        errors.append("output_height_pixels must be greater than zero.")
    if (
        window.read_width_pixels
        > window.output_width_pixels
    ):
        errors.append(
            "read_width_pixels must not exceed "
            "output_width_pixels."
        )
    if (
        window.read_height_pixels
        > window.output_height_pixels
    ):
        errors.append(
            "read_height_pixels must not exceed "
            "output_height_pixels."
        )
    if (
        window.output_width_pixels
        != layout.tile_width_pixels
    ):
        errors.append(
            "output_width_pixels must match "
            "layout.tile_width_pixels."
        )
    if (
        window.output_height_pixels
        != layout.tile_height_pixels
    ):
        errors.append(
            "output_height_pixels must match "
            "layout.tile_height_pixels."
        )
    if (
        window.column_offset_pixels >= 0
        and window.read_width_pixels > 0
        and (
            window.column_offset_pixels
            + window.read_width_pixels
            > grid.width
        )
    ):
        errors.append("tile window must not exceed grid.width.")
    if (
        window.row_offset_pixels >= 0
        and window.read_height_pixels > 0
        and (
            window.row_offset_pixels
            + window.read_height_pixels
            > grid.height
        )
    ):
        errors.append(
            "tile window must not exceed grid.height."
        )
    if (
        0 < window.read_width_pixels
        < window.output_width_pixels
        and (
            window.column_offset_pixels
            + window.read_width_pixels
            != grid.width
        )
    ):
        errors.append(
            "a partial-width window must touch "
            "the right grid edge."
        )
    if (
        0 < window.read_height_pixels
        < window.output_height_pixels
        and (
            window.row_offset_pixels
            + window.read_height_pixels
            != grid.height
        )
    ):
        errors.append(
            "a partial-height window must touch "
            "the bottom grid edge."
        )
    if (
        window.is_partial
        and layout.edge_policy
        != TileEdgePolicy.PAD_PARTIAL
    ):
        errors.append(
            "partial windows require the "
            "pad_partial edge policy."
        )
    return tuple(errors)


def validate_tile_window_identity(
    window: TileWindowSpec,
    *,
    grid_id: str,
    layout: TileLayoutSpec,
) -> tuple[str, ...]:
    "Verify that a tile ID represents the exact window content"
    if not window.tile_id.strip():
        return ("tile_id must not be empty.",)
    expected_tile_id = build_tile_window_id(
        grid_id=grid_id,
        layout=layout,
        row_index=window.row_index,
        column_index=window.column_index,
        row_offset_pixels=window.row_offset_pixels,
        column_offset_pixels=window.column_offset_pixels,
        read_width_pixels=window.read_width_pixels,
        read_height_pixels=window.read_height_pixels,
    )
    if window.tile_id != expected_tile_id:
        return (
            "tile_id must match the exact grid, layout, "
            "and window content.",
        )
    return ()


def validate_tiling_request(
    request: TilingRequest,
) -> tuple[str, ...]:
    "Return validation errors for one raster-tiling request"

    errors = list(
        validate_tile_layout(request.layout)
    )

    if (
        request.image_artifact_path
        == request.label_artifact_path
    ):
        errors.append(
            "image_artifact_path and label_artifact_path "
            "must be different."
        )

    if not request.grid_id.strip():
        errors.append("grid_id must not be empty.")

    if not request.output_name.strip():
        errors.append("output_name must not be empty.")

    grid_errors = validate_exact_raster_grid_spec(
        request.grid
    )
    errors.extend(grid_errors)

    if (
        request.grid_id.strip()
        and not grid_errors
        and request.grid_id
        != build_raster_grid_id(request.grid)
    ):
        errors.append(
            "grid_id must match the exact raster-grid identity."
        )

    if (
        request.layout.tile_width_pixels
        > request.grid.width
    ):
        errors.append(
            "tile_width_pixels must not exceed grid.width."
        )

    if (
        request.layout.tile_height_pixels
        > request.grid.height
    ):
        errors.append(
            "tile_height_pixels must not exceed grid.height."
        )

    return tuple(errors)