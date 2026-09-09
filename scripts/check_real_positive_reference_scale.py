"Measure real positive-reference geometry scale for tile-layout selection"
from math import pi
import numpy as np
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.label_rasterization import (
    load_real_reference_source_configs,
    wire_real_reference_sources,
)


TARGET_CRS = "EPSG:32639"
PIXEL_SIZE_METRES = 10.0
TILE_SIZES = (128, 256, 512)
QUANTILES = (0, 25, 50, 75, 90, 95, 100)


def print_distribution(name: str, values: np.ndarray) -> None:
    "Print selected quantiles for one geometry measurement"
    measured = np.percentile(values, QUANTILES)
    print(
        f"{name},"
        + ",".join(f"{value:.2f}" for value in measured)
    )


def main() -> int:
    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    wired_sources = wire_real_reference_sources(
        configs=configs,
        target_crs=TARGET_CRS,
    )

    positive_source = next(
        source
        for source in wired_sources
        if source.vector_source.supervision
        == SupervisionKind.POSITIVE_REFERENCE
    )
    geometries = positive_source.vector_source.geometries

    areas = np.array(
        [geometry.area for geometry in geometries],
        dtype=float,
    )
    bounds = np.array(
        [geometry.bounds for geometry in geometries],
        dtype=float,
    )
    widths = bounds[:, 2] - bounds[:, 0]
    heights = bounds[:, 3] - bounds[:, 1]
    maximum_spans = np.maximum(widths, heights)
    equivalent_diameters = 2.0 * np.sqrt(areas / pi)

    print("Loop 1 positive-reference scale analysis")
    print("========================================")
    print(f"Target CRS: {TARGET_CRS}")
    print(f"Feature count: {len(geometries)}")
    print()
    print("metric,min,p25,median,p75,p90,p95,max")
    print_distribution("area_square_metres", areas)
    print_distribution("width_metres", widths)
    print_distribution("height_metres", heights)
    print_distribution("maximum_span_metres", maximum_spans)
    print_distribution("equivalent_diameter_metres", equivalent_diameters)
    print()
    p95_span = float(np.percentile(maximum_spans, 95))

    print(
        "tile_pixels,footprint_metres,"
        "features_within_footprint,feature_percent,"
        "footprint_to_p95_span"
    )

    for tile_size in TILE_SIZES:
        footprint = tile_size * PIXEL_SIZE_METRES
        within_footprint = int(
            np.count_nonzero(
                (widths <= footprint) & (heights <= footprint)
            )
        )
        feature_percent = 100.0 * within_footprint / len(geometries)
        footprint_to_p95_span = footprint / p95_span

        print(
            f"{tile_size},"
            f"{footprint:.0f},"
            f"{within_footprint},"
            f"{feature_percent:.3f},"
            f"{footprint_to_p95_span:.3f}"
        )

    print()
    print(
        "tile_pixels,overlap_percent,stride_pixels,"
        "guaranteed_span_metres,"
        "features_guaranteed_by_span,feature_percent"
    )

    for tile_size in TILE_SIZES:
        tile_extent = tile_size * PIXEL_SIZE_METRES

        for overlap_percent in (0, 25, 50):
            stride_pixels = tile_size * (100 - overlap_percent) // 100
            stride_metres = stride_pixels * PIXEL_SIZE_METRES
            guaranteed_span = tile_extent - stride_metres

            if guaranteed_span <= 0:
                guaranteed_count = 0
            else:
                guaranteed_count = int(
                    np.count_nonzero(
                        (widths <= guaranteed_span)
                        & (heights <= guaranteed_span)
                    )
                )

            guaranteed_percent = (
                100.0 * guaranteed_count / len(geometries)
            )

            print(
                f"{tile_size},"
                f"{overlap_percent},"
                f"{stride_pixels},"
                f"{guaranteed_span:.0f},"
                f"{guaranteed_count},"
                f"{guaranteed_percent:.3f}"
            )

    if len(geometries) != 57:
        print()
        print("FAIL: Positive-reference feature count is not 57.")
        return 1

    print()
    print("PASS: Positive-reference scale analysis completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())