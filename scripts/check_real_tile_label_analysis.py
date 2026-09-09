"Compare tile-layout candidates against the real Loop 1 label raster"
import csv
import sys
from pathlib import Path
import rasterio
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
    analyze_label_tiles,
)


IMAGE_PATH = Path("artifacts/live/loop1/komeh_sentinel2_2024_median.tif")
LABEL_PATH = Path("artifacts/live/loop1/komeh_labels_v1.tif")

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

EXPECTED_GRID_ID = (
    "sha256:"
    "d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799"
)

TILE_SIZES = (128, 256, 512)

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
        grid_id=build_raster_grid_id(APPROVED_GRID),
        layout=TileLayoutSpec(
            tile_width_pixels=tile_size,
            tile_height_pixels=tile_size,
            stride_x_pixels=stride,
            stride_y_pixels=stride,
            edge_policy=edge_policy,
        ),
        output_name=f"komeh-{tile_size}-{stride}-{edge_policy.value}",
    )


def main() -> int:
    actual_grid_id = build_raster_grid_id(APPROVED_GRID)

    if actual_grid_id != EXPECTED_GRID_ID:
        print("FAIL: Approved grid identity does not match the manifest.")
        return 1

    if not LABEL_PATH.is_file():
        print(f"FAIL: Label raster does not exist: {LABEL_PATH}")
        return 1

    with rasterio.open(LABEL_PATH) as dataset:
        labels = dataset.read(1)

    print("Loop 1 real label-aware tiling analysis")
    print("========================================")
    print(f"Label path: {LABEL_PATH}")
    print(f"Label shape: {labels.shape}")
    print(f"Grid ID matches manifest: {actual_grid_id == EXPECTED_GRID_ID}")
    print()

    writer = csv.writer(sys.stdout)
    writer.writerow(
        [
            "tile_size",
            "stride",
            "overlap_percent",
            "edge_policy",
            "tile_count",
            "supervised_tiles",
            "positive_tiles",
            "negative_only_tiles",
            "all_ignore_tiles",
            "positive_tiles_ge_1pct",
            "positive_tiles_ge_5pct",
            "positive_coverage_percent",
            "negative_coverage_percent",
            "positive_observation_multiplier",
            "padded_ignore_pixels",
        ]
    )

    for tile_size in TILE_SIZES:
        for stride in (tile_size, 3 * tile_size // 4, tile_size // 2):
            overlap_percent = 100 * (tile_size - stride) / tile_size

            for edge_policy in EDGE_POLICIES:
                request = make_request(
                    tile_size=tile_size,
                    stride=stride,
                    edge_policy=edge_policy,
                )
                result = analyze_label_tiles(labels, request)

                writer.writerow(
                    [
                        tile_size,
                        stride,
                        f"{overlap_percent:.0f}",
                        edge_policy.value,
                        result.tile_count,
                        result.supervised_tile_count,
                        result.positive_tile_count,
                        result.negative_only_tile_count,
                        result.all_ignore_tile_count,
                        result.positive_tiles_at_least_one_percent,
                        result.positive_tiles_at_least_five_percent,
                        f"{result.positive_coverage_ratio:.6%}",
                        f"{result.negative_coverage_ratio:.6%}",
                        f"{result.positive_observation_multiplier:.3f}",
                        result.padded_ignore_pixel_observations,
                    ]
                )
    print()
    print("PASS: Real label-aware tiling analysis completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())