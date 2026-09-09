"Compare candidate tiling layouts on the real Loop 1 raster grid"
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
)


IMAGE_PATH = Path(
    "artifacts/live/loop1/"
    "komeh_sentinel2_2024_median.tif"
)
LABEL_PATH = Path(
    "artifacts/live/loop1/"
    "komeh_labels_v1.tif"
)

APPROVED_GRID = RasterGridSpec(
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

TILE_SIZES = (
    128,
    256,
    512,
)

EDGE_POLICIES = (
    TileEdgePolicy.DROP_PARTIAL,
    TileEdgePolicy.PAD_PARTIAL,
    TileEdgePolicy.SHIFT_TO_FIT,
)


def make_request(
    *,
    tile_size: int,
    stride: int,
    edge_policy: TileEdgePolicy,
) -> TilingRequest:
    return TilingRequest(
        image_artifact_path=IMAGE_PATH,
        label_artifact_path=LABEL_PATH,
        grid=APPROVED_GRID,
        grid_id=build_raster_grid_id(
            APPROVED_GRID
        ),
        layout=TileLayoutSpec(
            tile_width_pixels=tile_size,
            tile_height_pixels=tile_size,
            stride_x_pixels=stride,
            stride_y_pixels=stride,
            edge_policy=edge_policy,
        ),
        output_name=(
            f"komeh-{tile_size}-"
            f"{stride}-{edge_policy.value}"
        ),
    )


def main() -> int:
    expected_grid_id = (
        "sha256:"
        "d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799"
    )
    actual_grid_id = build_raster_grid_id(APPROVED_GRID)
    print("Loop 1 candidate tiling geometry")
    print("================================")
    print(f"Grid ID matches manifest: {actual_grid_id == expected_grid_id}")
    print(f"Raster dimensions: {APPROVED_GRID.width} x {APPROVED_GRID.height}")
    print()

    header = (
        f"{'tile':>6} "
        f"{'stride':>6} "
        f"{'overlap':>8} "
        f"{'edge':>14} "
        f"{'tiles':>7} "
        f"{'partial':>8} "
        f"{'coverage':>9} "
        f"{'uncovered':>11} "
        f"{'padding':>11} "
        f"{'repeated':>11} "
        f"{'expansion':>10}"
    )
    print(header)
    print("-" * len(header))

    for tile_size in TILE_SIZES:
        for stride in (tile_size, 3 * tile_size // 4, tile_size // 2):
            overlap_percent = (
                100
                * (tile_size - stride)
                / tile_size
            )

            for edge_policy in EDGE_POLICIES:
                request = make_request(
                    tile_size=tile_size,
                    stride=stride,
                    edge_policy=edge_policy,
                )
                result = analyze_tile_layout(request)
                print(
                    f"{tile_size:>6} "
                    f"{stride:>6} "
                    f"{overlap_percent:>7.0f}% "
                    f"{edge_policy.value:>14} "
                    f"{result.tile_count:>7} "
                    f"{result.partial_tile_count:>8} "
                    f"{result.coverage_ratio:>8.3%} "
                    f"{result.uncovered_source_pixel_count:>11,} "
                    f"{result.padded_output_pixel_count:>11,} "
                    f"{result.repeated_read_pixel_count:>11,} "
                    f"{result.output_expansion_ratio:>9.3f}x"
                )

    print()
    print(
        "PASS: Candidate layout geometry was "
        "computed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )