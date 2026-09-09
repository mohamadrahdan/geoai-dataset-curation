"Measure actual positive-feature containment in candidate tile layouts"

from pathlib import Path

from affine import Affine
from rasterio.windows import Window, bounds

from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.label_rasterization import (
    load_real_reference_source_configs,
    wire_real_reference_sources,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TilingRequest,
    generate_tile_windows,
)


IMAGE_PATH = Path(
    "artifacts/live/loop1/komeh_sentinel2_2024_median.tif"
)
LABEL_PATH = Path(
    "artifacts/live/loop1/komeh_labels_v1.tif"
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

TILE_SIZES = (128, 256, 512)
OVERLAP_PERCENTAGES = (0, 25, 50)
CONTEXT_MARGINS_METRES = (0.0, 160.0, 320.0)


def make_request(tile_size: int, stride: int) -> TilingRequest:
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
            edge_policy=TileEdgePolicy.SHIFT_TO_FIT,
        ),
        output_name=f"containment-{tile_size}-{stride}",
    )


def build_window_bounds(request: TilingRequest) -> tuple[tuple[float, ...], ...]:
    transform_spec = request.grid.transform

    if transform_spec is None:
        raise ValueError("Exact grid transform is required.")

    transform = Affine(*transform_spec.as_tuple)
    tile_windows = generate_tile_windows(request)

    return tuple(
        bounds(
            Window.from_slices(
                rows=(
                    window.row_offset_pixels,
                    window.row_offset_pixels + window.read_height_pixels,
                ),
                cols=(
                    window.column_offset_pixels,
                    window.column_offset_pixels + window.read_width_pixels,
                ),
            ),
            transform,
        )
        for window in tile_windows
    )


def feature_is_contained(
    feature_bounds: tuple[float, float, float, float],
    candidate_bounds: tuple[tuple[float, ...], ...],
    context_margin: float,
) -> bool:
    min_x, min_y, max_x, max_y = feature_bounds
    required_left = min_x - context_margin
    required_bottom = min_y - context_margin
    required_right = max_x + context_margin
    required_top = max_y + context_margin

    return any(
        left <= required_left
        and bottom <= required_bottom
        and right >= required_right
        and top >= required_top
        for left, bottom, right, top in candidate_bounds
    )


def main() -> int:
    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    wired_sources = wire_real_reference_sources(
        configs=configs,
        target_crs=APPROVED_GRID.crs,
    )
    positive_source = next(
        source
        for source in wired_sources
        if source.vector_source.supervision
        == SupervisionKind.POSITIVE_REFERENCE
    )
    geometries = positive_source.vector_source.geometries

    print("Loop 1 actual positive-feature containment")
    print("==========================================")
    print(f"Feature count: {len(geometries)}")
    print()
    print(
        "tile_pixels,stride_pixels,overlap_percent,"
        "context_margin_metres,contained_features,"
        "contained_percent,tile_count"
    )

    for tile_size in TILE_SIZES:
        for overlap_percent in OVERLAP_PERCENTAGES:
            stride = tile_size * (100 - overlap_percent) // 100
            request = make_request(tile_size, stride)
            candidate_bounds = build_window_bounds(request)

            for context_margin in CONTEXT_MARGINS_METRES:
                contained_count = sum(
                    feature_is_contained(
                        geometry.bounds,
                        candidate_bounds,
                        context_margin,
                    )
                    for geometry in geometries
                )
                contained_percent = 100.0 * contained_count / len(geometries)

                print(
                    f"{tile_size},"
                    f"{stride},"
                    f"{overlap_percent},"
                    f"{context_margin:.0f},"
                    f"{contained_count},"
                    f"{contained_percent:.3f},"
                    f"{len(candidate_bounds)}"
                )

    if len(geometries) != 57:
        print()
        print("FAIL: Positive-reference feature count is not 57.")
        return 1

    print()
    print("PASS: Actual positive-feature containment completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())