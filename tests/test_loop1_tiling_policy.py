from pathlib import Path
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling import (
    LOOP1_TILING_LAYOUT,
    TileEdgePolicy,
    TilingRequest,
    analyze_tile_layout,
    validate_tile_layout,
)


def make_real_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=5712,
        height=5493,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=533040.0,
            d=0.0,
            e=-10.0,
            f=3451350.0,
        ),
    )


def test_loop1_tiling_layout_has_selected_parameters() -> None:
    assert LOOP1_TILING_LAYOUT.tile_width_pixels == 256
    assert LOOP1_TILING_LAYOUT.tile_height_pixels == 256
    assert LOOP1_TILING_LAYOUT.stride_x_pixels == 192
    assert LOOP1_TILING_LAYOUT.stride_y_pixels == 192
    assert LOOP1_TILING_LAYOUT.edge_policy == TileEdgePolicy.SHIFT_TO_FIT
    assert (
        LOOP1_TILING_LAYOUT.tile_width_pixels
        - LOOP1_TILING_LAYOUT.stride_x_pixels
        == 64
    )


def test_loop1_tiling_layout_is_valid() -> None:
    assert validate_tile_layout(LOOP1_TILING_LAYOUT) == ()


def test_loop1_tiling_layout_covers_the_real_grid() -> None:
    grid = make_real_grid()
    request = TilingRequest(
        image_artifact_path=Path("artifacts/image.tif"),
        label_artifact_path=Path("artifacts/labels.tif"),
        grid=grid,
        grid_id=build_raster_grid_id(grid),
        layout=LOOP1_TILING_LAYOUT,
        output_name="loop1-selected-layout",
    )

    result = analyze_tile_layout(request)
    assert result.tile_count == 870
    assert result.full_tile_count == 870
    assert result.partial_tile_count == 0
    assert result.coverage_ratio == 1.0
    assert result.uncovered_source_pixel_count == 0
    assert result.padded_output_pixel_count == 0