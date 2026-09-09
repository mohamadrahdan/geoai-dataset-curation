from dataclasses import replace
from pathlib import Path
import pytest
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TilingRequest,
    generate_tile_windows,
    validate_tile_window_identity,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=5712,
        height=5493,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=547020.0,
            d=0.0,
            e=-10.0,
            f=3374300.0,
        ),
    )


def make_request(
    edge_policy: TileEdgePolicy,
) -> TilingRequest:
    grid = make_grid()
    return TilingRequest(
        image_artifact_path=Path("artifacts/live/loop1/image.tif"),
        label_artifact_path=Path("artifacts/live/loop1/labels.tif"),
        grid=grid,
        grid_id=build_raster_grid_id(grid),
        layout=TileLayoutSpec(
            tile_width_pixels=256,
            tile_height_pixels=256,
            stride_x_pixels=256,
            stride_y_pixels=256,
            edge_policy=edge_policy,
        ),
        output_name="candidate-tiles",
    )


def test_drop_partial_generates_only_full_windows() -> None:
    request = make_request(
        TileEdgePolicy.DROP_PARTIAL
    )
    windows = generate_tile_windows(request)
    assert len(windows) == 462
    assert all(
        window.is_partial is False
        for window in windows
    )
    last = windows[-1]
    assert last.row_index == 20
    assert last.column_index == 21
    assert last.row_offset_pixels == 5120
    assert last.column_offset_pixels == 5376


def test_pad_partial_covers_real_raster_edges() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    windows = generate_tile_windows(request)
    assert len(windows) == 506
    last = windows[-1]
    assert last.row_index == 21
    assert last.column_index == 22
    assert last.row_offset_pixels == 5376
    assert last.column_offset_pixels == 5632
    assert last.read_width_pixels == 80
    assert last.read_height_pixels == 117
    assert last.padding_right_pixels == 176
    assert last.padding_bottom_pixels == 139
    assert last.is_partial is True


def test_shift_to_fit_generates_full_edge_windows() -> None:
    request = make_request(TileEdgePolicy.SHIFT_TO_FIT)
    windows = generate_tile_windows(request)
    assert len(windows) == 506
    assert all(
        window.is_partial is False
        for window in windows
    )
    last = windows[-1]
    assert last.row_index == 21
    assert last.column_index == 22
    assert last.row_offset_pixels == 5237
    assert last.column_offset_pixels == 5456
    assert last.read_width_pixels == 256
    assert last.read_height_pixels == 256


def test_windows_are_generated_in_row_major_order() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    windows = generate_tile_windows(request)
    assert windows[0].row_index == 0
    assert windows[0].column_index == 0
    assert windows[22].row_index == 0
    assert windows[22].column_index == 22
    assert windows[23].row_index == 1
    assert windows[23].column_index == 0


def test_repeated_generation_is_deterministic() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    first = generate_tile_windows(request)
    second = generate_tile_windows(request)
    assert first == second


def test_generated_window_identities_are_valid() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    windows = generate_tile_windows(request)
    assert all(
        validate_tile_window_identity(
            window,
            grid_id=request.grid_id,
            layout=request.layout,
        )
        == ()
        for window in windows
    )


def test_generation_rejects_invalid_request() -> None:
    request = make_request(
        TileEdgePolicy.DROP_PARTIAL
    )
    invalid_request = replace(
        request,
        grid_id="sha256:not-the-grid-id",
    )
    with pytest.raises(
        ValueError,
        match="Invalid tiling request",
    ):
        generate_tile_windows(invalid_request)