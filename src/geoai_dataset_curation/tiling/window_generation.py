"Deterministic generation of candidate tile windows"
from geoai_dataset_curation.tiling.contracts import (
    TileEdgePolicy,
    TileWindowSpec,
    TilingRequest,
)
from geoai_dataset_curation.tiling.identity import (
    build_tile_window_id,
)
from geoai_dataset_curation.tiling.validation import (
    validate_tile_window,
    validate_tile_window_identity,
    validate_tiling_request,
)


def _generate_axis_windows(
    *,
    source_length: int,
    tile_length: int,
    stride: int,
    edge_policy: TileEdgePolicy,
) -> tuple[tuple[int, int], ...]:
    "Generate ordered offset and read-length pairs for one axis"
    full_limit = source_length - tile_length
    if edge_policy == TileEdgePolicy.DROP_PARTIAL:
        return tuple(
            (offset, tile_length)
            for offset in range(
                0,
                full_limit + 1,
                stride,
            )
        )

    if edge_policy == TileEdgePolicy.PAD_PARTIAL:
        return tuple(
            (
                offset,
                min(
                    tile_length,
                    source_length - offset,
                ),
            )
            for offset in range(
                0,
                source_length,
                stride,
            )
        )

    if edge_policy == TileEdgePolicy.SHIFT_TO_FIT:
        offsets = list(
            range(
                0,
                full_limit + 1,
                stride,
            )
        )
        if offsets[-1] != full_limit:
            offsets.append(full_limit)
        return tuple(
            (offset, tile_length)
            for offset in offsets
        )
    raise ValueError(
        f"Unsupported tile edge policy: {edge_policy!r}"
    )


def generate_tile_windows(
    request: TilingRequest,
) -> tuple[TileWindowSpec, ...]:
    "Generate deterministic row-major windows for one tiling request"
    request_errors = validate_tiling_request(
        request
    )
    if request_errors:
        raise ValueError(
            "Invalid tiling request: "
            + "; ".join(request_errors)
        )
    layout = request.layout
    grid = request.grid

    column_windows = _generate_axis_windows(
        source_length=grid.width,
        tile_length=layout.tile_width_pixels,
        stride=layout.stride_x_pixels,
        edge_policy=layout.edge_policy,
    )
    row_windows = _generate_axis_windows(
        source_length=grid.height,
        tile_length=layout.tile_height_pixels,
        stride=layout.stride_y_pixels,
        edge_policy=layout.edge_policy,
    )
    windows: list[TileWindowSpec] = []

    for row_index, (
        row_offset,
        read_height,
    ) in enumerate(row_windows):
        for column_index, (
            column_offset,
            read_width,
        ) in enumerate(column_windows):
            tile_id = build_tile_window_id(
                grid_id=request.grid_id,
                layout=layout,
                row_index=row_index,
                column_index=column_index,
                row_offset_pixels=row_offset,
                column_offset_pixels=column_offset,
                read_width_pixels=read_width,
                read_height_pixels=read_height,
            )
            window = TileWindowSpec(
                tile_id=tile_id,
                row_index=row_index,
                column_index=column_index,
                row_offset_pixels=row_offset,
                column_offset_pixels=column_offset,
                read_width_pixels=read_width,
                read_height_pixels=read_height,
                output_width_pixels=(
                    layout.tile_width_pixels
                ),
                output_height_pixels=(
                    layout.tile_height_pixels
                ),
            )
            window_errors = validate_tile_window(
                window,
                grid=grid,
                layout=layout,
            )
            identity_errors = validate_tile_window_identity(
                window,
                grid_id=request.grid_id,
                layout=layout,
            )
            if window_errors or identity_errors:
                raise RuntimeError(
                    "Generated invalid tile window: "
                    + "; ".join(
                        window_errors
                        + identity_errors
                    )
                )
            windows.append(window)
    return tuple(windows)