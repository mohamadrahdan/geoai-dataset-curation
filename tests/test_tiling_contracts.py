from pathlib import Path
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TilingRequest,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TileWindowSpec,
    TilingRequest,
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


def test_tile_layout_preserves_spatial_parameters() -> None:
    layout = TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=128,
        stride_y_pixels=128,
        edge_policy=TileEdgePolicy.PAD_PARTIAL,
    )
    assert layout.tile_width_pixels == 256
    assert layout.tile_height_pixels == 256
    assert layout.stride_x_pixels == 128
    assert layout.stride_y_pixels == 128
    assert layout.edge_policy == TileEdgePolicy.PAD_PARTIAL


def test_tiling_request_preserves_aligned_pair_identity() -> None:
    grid = make_grid()
    layout = TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=256,
        stride_y_pixels=256,
        edge_policy=TileEdgePolicy.DROP_PARTIAL,
    )
    request = TilingRequest(
        image_artifact_path=Path(
            "artifacts/live/loop1/image.tif"
        ),
        label_artifact_path=Path(
            "artifacts/live/loop1/labels.tif"
        ),
        grid=grid,
        grid_id="sha256:test-grid",
        layout=layout,
        output_name="loop1-candidate-tiles",
    )
    assert request.grid is grid
    assert request.layout is layout
    assert request.grid_id == "sha256:test-grid"
    assert request.image_artifact_path.name == "image.tif"
    assert request.label_artifact_path.name == "labels.tif"
    assert request.output_name == "loop1-candidate-tiles"


def test_full_tile_window_requires_no_padding() -> None:
    window = TileWindowSpec(
        tile_id="r0000-c0000",
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=256,
        read_height_pixels=256,
        output_width_pixels=256,
        output_height_pixels=256,
    )
    assert window.padding_right_pixels == 0
    assert window.padding_bottom_pixels == 0
    assert window.is_partial is False


def test_partial_edge_window_reports_required_padding() -> None:
    window = TileWindowSpec(
        tile_id="r0021-c0022",
        row_index=21,
        column_index=22,
        row_offset_pixels=5376,
        column_offset_pixels=5632,
        read_width_pixels=80,
        read_height_pixels=117,
        output_width_pixels=256,
        output_height_pixels=256,
    )
    assert window.padding_right_pixels == 176
    assert window.padding_bottom_pixels == 139
    assert window.is_partial is True