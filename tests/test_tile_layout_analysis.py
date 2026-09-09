from pathlib import Path
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
    analyze_tile_layout,
    build_tile_layout_id,
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
    *,
    stride: int = 256,
) -> TilingRequest:
    grid = make_grid()

    return TilingRequest(
        image_artifact_path=Path(
            "artifacts/live/loop1/image.tif"
        ),
        label_artifact_path=Path(
            "artifacts/live/loop1/labels.tif"
        ),
        grid=grid,
        grid_id=build_raster_grid_id(grid),
        layout=TileLayoutSpec(
            tile_width_pixels=256,
            tile_height_pixels=256,
            stride_x_pixels=stride,
            stride_y_pixels=stride,
            edge_policy=edge_policy,
        ),
        output_name="candidate-layout-analysis",
    )


def test_drop_partial_reports_uncovered_edge_pixels() -> None:
    request = make_request(
        TileEdgePolicy.DROP_PARTIAL
    )
    result = analyze_tile_layout(request)
    assert result.tile_count == 462
    assert result.full_tile_count == 462
    assert result.partial_tile_count == 0
    assert result.source_pixel_count == 31_376_016
    assert (
        result.covered_source_pixel_count
        == 30_277_632
    )
    assert (
        result.uncovered_source_pixel_count
        == 1_098_384
    )
    assert result.padded_output_pixel_count == 0
    assert result.repeated_read_pixel_count == 0
    assert result.coverage_ratio < 1.0


def test_pad_partial_reports_padding_cost() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    result = analyze_tile_layout(request)
    assert result.tile_count == 506
    assert result.full_tile_count == 462
    assert result.partial_tile_count == 44
    assert (
        result.covered_source_pixel_count
        == 31_376_016
    )
    assert result.uncovered_source_pixel_count == 0
    assert result.total_read_pixel_count == 31_376_016
    assert result.total_output_pixel_count == 33_161_216
    assert result.padded_output_pixel_count == 1_785_200
    assert result.repeated_read_pixel_count == 0
    assert result.coverage_ratio == 1.0


def test_shift_to_fit_reports_repeated_edge_reads() -> None:
    request = make_request(
        TileEdgePolicy.SHIFT_TO_FIT
    )
    result = analyze_tile_layout(request)
    assert result.tile_count == 506
    assert result.full_tile_count == 506
    assert result.partial_tile_count == 0
    assert (
        result.covered_source_pixel_count
        == 31_376_016
    )
    assert result.uncovered_source_pixel_count == 0
    assert result.total_read_pixel_count == 33_161_216
    assert result.padded_output_pixel_count == 0
    assert result.repeated_read_pixel_count == 1_785_200
    assert result.coverage_ratio == 1.0


def test_overlapping_layout_increases_output_cost() -> None:
    nonoverlapping = analyze_tile_layout(
        make_request(
            TileEdgePolicy.PAD_PARTIAL,
            stride=256,
        )
    )
    overlapping = analyze_tile_layout(
        make_request(
            TileEdgePolicy.PAD_PARTIAL,
            stride=128,
        )
    )
    assert overlapping.tile_count == 1935
    assert overlapping.coverage_ratio == 1.0
    assert (
        overlapping.repeated_read_pixel_count
        > nonoverlapping.repeated_read_pixel_count
    )
    assert (
        overlapping.output_expansion_ratio
        > nonoverlapping.output_expansion_ratio
    )


def test_analysis_preserves_stable_layout_identity() -> None:
    request = make_request(
        TileEdgePolicy.PAD_PARTIAL
    )
    result = analyze_tile_layout(request)
    assert result.layout_id == build_tile_layout_id(
        request.layout
    )