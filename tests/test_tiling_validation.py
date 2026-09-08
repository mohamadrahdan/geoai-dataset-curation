from pathlib import Path
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TileWindowSpec,
    TilingRequest,
    build_tile_window_id,
    validate_tile_layout,
    validate_tile_window,
    validate_tile_window_identity,
    validate_tiling_request,
)
import pytest
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)


def make_grid(
    *,
    width: int = 5712,
    height: int = 5493,
    transform: AffineTransformSpec | None = None,
) -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=width,
        height=height,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=transform
        or AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=547020.0,
            d=0.0,
            e=-10.0,
            f=3374300.0,
        ),
    )


def make_layout(
    *,
    tile_width: int = 256,
    tile_height: int = 256,
    stride_x: int = 256,
    stride_y: int = 256,
) -> TileLayoutSpec:
    return TileLayoutSpec(
        tile_width_pixels=tile_width,
        tile_height_pixels=tile_height,
        stride_x_pixels=stride_x,
        stride_y_pixels=stride_y,
        edge_policy=TileEdgePolicy.DROP_PARTIAL,
    )


def make_request(
    *,
    grid: RasterGridSpec | None = None,
    layout: TileLayoutSpec | None = None,
    grid_id: str | None = None,
    output_name: str = "candidate-tiles",
    same_paths: bool = False,
) -> TilingRequest:
    selected_grid = grid or make_grid()
    image_path = Path("artifacts/image.tif")
    label_path = (
        image_path
        if same_paths
        else Path("artifacts/labels.tif")
    )

    return TilingRequest(
        image_artifact_path=image_path,
        label_artifact_path=label_path,
        grid=selected_grid,
        grid_id=(
            grid_id
            if grid_id is not None
            else build_raster_grid_id(selected_grid)
        ),
        layout=layout or make_layout(),
        output_name=output_name,
    )


def make_window(
    *,
    tile_id: str = "r0000-c0000",
    row_index: int = 0,
    column_index: int = 0,
    row_offset: int = 0,
    column_offset: int = 0,
    read_width: int = 256,
    read_height: int = 256,
    output_width: int = 256,
    output_height: int = 256,
) -> TileWindowSpec:
    return TileWindowSpec(
        tile_id=tile_id,
        row_index=row_index,
        column_index=column_index,
        row_offset_pixels=row_offset,
        column_offset_pixels=column_offset,
        read_width_pixels=read_width,
        read_height_pixels=read_height,
        output_width_pixels=output_width,
        output_height_pixels=output_height,
    )


def test_validate_tile_layout_accepts_valid_layout() -> None:
    errors = validate_tile_layout(
        make_layout(
            stride_x=128,
            stride_y=128,
        )
    )
    assert errors == ()


def test_validate_tile_layout_rejects_nonpositive_dimensions() -> None:
    errors = validate_tile_layout(
        make_layout(
            tile_width=0,
            tile_height=-1,
        )
    )
    assert (
        "tile_width_pixels must be greater than zero."
        in errors
    )
    assert (
        "tile_height_pixels must be greater than zero."
        in errors
    )


def test_validate_tile_layout_rejects_nonpositive_strides() -> None:
    errors = validate_tile_layout(
        make_layout(
            stride_x=0,
            stride_y=-1,
        )
    )
    assert (
        "stride_x_pixels must be greater than zero."
        in errors
    )
    assert (
        "stride_y_pixels must be greater than zero."
        in errors
    )


def test_validate_tile_layout_rejects_spatial_gaps() -> None:
    errors = validate_tile_layout(
        make_layout(
            tile_width=256,
            tile_height=256,
            stride_x=257,
            stride_y=300,
        )
    )

    assert (
        "stride_x_pixels must not exceed "
        "tile_width_pixels."
        in errors
    )
    assert (
        "stride_y_pixels must not exceed "
        "tile_height_pixels."
        in errors
    )


def test_validate_tiling_request_accepts_valid_request() -> None:
    errors = validate_tiling_request(
        make_request()
    )
    assert errors == ()


def test_validate_tiling_request_rejects_invalid_identity() -> None:
    errors = validate_tiling_request(
        make_request(
            grid_id=" ",
            output_name=" ",
            same_paths=True,
        )
    )
    assert "grid_id must not be empty." in errors
    assert "output_name must not be empty." in errors
    assert (
        "image_artifact_path and label_artifact_path "
        "must be different."
        in errors
    )


def test_validate_tiling_request_requires_exact_suitable_grid() -> None:
    grid = make_grid(
        width=128,
        height=100,
    )
    layout = make_layout(
        tile_width=256,
        tile_height=256,
    )

    errors = validate_tiling_request(
        make_request(
            grid=grid,
            layout=layout,
        )
    )
    assert (
        "tile_width_pixels must not exceed grid.width."
        in errors
    )
    assert (
        "tile_height_pixels must not exceed grid.height."
        in errors
    )


def test_validate_tile_window_accepts_full_window() -> None:
    errors = validate_tile_window(
        make_window(),
        grid=make_grid(),
        layout=make_layout(),
    )
    assert errors == ()


def test_validate_tile_window_accepts_padded_edge_window() -> None:
    layout = TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=256,
        stride_y_pixels=256,
        edge_policy=TileEdgePolicy.PAD_PARTIAL,
    )
    window = make_window(
        tile_id="r0021-c0022",
        row_index=21,
        column_index=22,
        row_offset=5376,
        column_offset=5632,
        read_width=80,
        read_height=117,
    )
    errors = validate_tile_window(
        window,
        grid=make_grid(),
        layout=layout,
    )
    assert errors == ()


def test_validate_tile_window_rejects_invalid_identity_and_position() -> None:
    window = make_window(
        tile_id=" ",
        row_index=-1,
        column_index=-2,
        row_offset=-10,
        column_offset=-20,
    )
    errors = validate_tile_window(
        window,
        grid=make_grid(),
        layout=make_layout(),
    )
    assert "tile_id must not be empty." in errors
    assert (
        "row_index must be greater than or equal to zero."
        in errors
    )
    assert (
        "column_index must be greater than or equal to zero."
        in errors
    )
    assert (
        "row_offset_pixels must be greater than or equal to zero."
        in errors
    )
    assert (
        "column_offset_pixels must be greater than or equal to zero."
        in errors
    )


def test_validate_tile_window_rejects_inconsistent_dimensions() -> None:
    nonpositive_errors = validate_tile_window(
        make_window(
            read_width=0,
            output_height=0,
        ),
        grid=make_grid(),
        layout=make_layout(),
    )
    excessive_read_errors = validate_tile_window(
        make_window(
            read_width=257,
            read_height=300,
        ),
        grid=make_grid(),
        layout=make_layout(),
    )
    output_mismatch_errors = validate_tile_window(
        make_window(
            read_width=128,
            output_width=128,
        ),
        grid=make_grid(),
        layout=make_layout(),
    )
    assert (
        "read_width_pixels must be greater than zero."
        in nonpositive_errors
    )
    assert (
        "output_height_pixels must be greater than zero."
        in nonpositive_errors
    )
    assert (
        "read_width_pixels must not exceed "
        "output_width_pixels."
        in excessive_read_errors
    )
    assert (
        "read_height_pixels must not exceed "
        "output_height_pixels."
        in excessive_read_errors
    )
    assert (
        "output_width_pixels must match "
        "layout.tile_width_pixels."
        in output_mismatch_errors
    )


def test_validate_tile_window_rejects_invalid_grid_placement() -> None:
    outside_errors = validate_tile_window(
        make_window(
            row_offset=5300,
            column_offset=5600,
        ),
        grid=make_grid(),
        layout=make_layout(),
    )
    interior_partial_errors = validate_tile_window(
        make_window(
            row_offset=100,
            column_offset=100,
            read_width=80,
            read_height=117,
        ),
        grid=make_grid(),
        layout=TileLayoutSpec(
            tile_width_pixels=256,
            tile_height_pixels=256,
            stride_x_pixels=256,
            stride_y_pixels=256,
            edge_policy=TileEdgePolicy.PAD_PARTIAL,
        ),
    )
    assert (
        "tile window must not exceed grid.width."
        in outside_errors
    )
    assert (
        "tile window must not exceed grid.height."
        in outside_errors
    )
    assert (
        "a partial-width window must touch "
        "the right grid edge."
        in interior_partial_errors
    )
    assert (
        "a partial-height window must touch "
        "the bottom grid edge."
        in interior_partial_errors
    )


@pytest.mark.parametrize(
    "edge_policy",
    [
        TileEdgePolicy.DROP_PARTIAL,
        TileEdgePolicy.SHIFT_TO_FIT,
    ],
)
def test_partial_window_requires_padding_policy(
    edge_policy: TileEdgePolicy,
) -> None:
    layout = TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=256,
        stride_y_pixels=256,
        edge_policy=edge_policy,
    )
    window = make_window(
        row_offset=5376,
        column_offset=5632,
        read_width=80,
        read_height=117,
    )
    errors = validate_tile_window(
        window,
        grid=make_grid(),
        layout=layout,
    )
    assert (
        "partial windows require the "
        "pad_partial edge policy."
        in errors
    )


def test_validate_tiling_request_rejects_mismatched_grid_id() -> None:
    errors = validate_tiling_request(
        make_request(grid_id="sha256:not-the-real-grid-id",)
    )
    assert (
        "grid_id must match the exact raster-grid identity."
        in errors
    )


def test_validate_tile_window_identity_accepts_exact_identity() -> None:
    layout = make_layout()
    tile_id = build_tile_window_id(
        grid_id="sha256:test-grid",
        layout=layout,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=256,
        read_height_pixels=256,
    )
    window = make_window(tile_id=tile_id,)
    errors = validate_tile_window_identity(
        window,
        grid_id="sha256:test-grid",
        layout=layout,
    )
    assert errors == ()


def test_validate_tile_window_identity_rejects_changed_content() -> None:
    layout = make_layout()
    original_tile_id = build_tile_window_id(
        grid_id="sha256:test-grid",
        layout=layout,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=256,
        read_height_pixels=256,
    )
    changed_window = make_window(
        tile_id=original_tile_id,
        row_index=1,
        row_offset=256,
    )
    errors = validate_tile_window_identity(
        changed_window,
        grid_id="sha256:test-grid",
        layout=layout,
    )
    assert errors == (
        "tile_id must match the exact grid, layout, "
        "and window content.",
    )


def test_validate_tile_layout_rejects_unsupported_edge_policy() -> None:
    layout = TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=256,
        stride_y_pixels=256,
        edge_policy="unsupported",  # type: ignore[arg-type]
    )

    errors = validate_tile_layout(layout)

    assert (
        "edge_policy must be a TileEdgePolicy."
        in errors
    )