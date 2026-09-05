"Live statistics and spatial QC for the real Loop 1 label supervision"
from pathlib import Path
import rasterio
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    analyze_source_spatial_qc,
    compute_label_pixel_statistics,
    load_real_reference_source_configs,
    wire_real_reference_sources,
    compute_source_overlap_pixel_count,
)


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


def main() -> int:
    with rasterio.open(LABEL_PATH) as dataset:
        labels = dataset.read(1)
    statistics = compute_label_pixel_statistics(labels)

    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    wired_sources = wire_real_reference_sources(
        configs=configs,
        target_crs=APPROVED_GRID.crs,
    )
    sources_by_id = {
        wired.vector_source.source_id: wired.vector_source
        for wired in wired_sources
    }
    negative_hard_negative_overlap = compute_source_overlap_pixel_count(
        sources_by_id["negative-reference"],
        sources_by_id["hard-negative-reference"],
        APPROVED_GRID,
    )

    print()
    print(
        "Negative / hard-negative overlap pixels: "
        f"{negative_hard_negative_overlap}"
    )

    print("Real label statistics and spatial QC")
    print("=====================")
    print(f"Label: {LABEL_PATH}")
    print()
    print(f"Total pixels: {statistics.total_pixels}")
    print(f"Supervised pixels: {statistics.supervised_pixels}")
    print(f"Positive pixels: {statistics.positive_pixels}")
    print(f"Negative pixels: {statistics.negative_pixels}")
    print(f"Ignore pixels: {statistics.ignore_pixels}")
    print(
        "Supervised fraction: "
        f"{statistics.supervised_fraction:.6%}"
    )
    print(
        "Positive fraction of supervised: "
        f"{statistics.positive_fraction_of_supervised:.6%}"
    )
    print(
        "Negative fraction of supervised: "
        f"{statistics.negative_fraction_of_supervised:.6%}"
    )

    print()
    print("Source spatial QC")
    print("----------")

    total_disjoint = 0
    for wired in wired_sources:
        result = analyze_source_spatial_qc(
            wired.vector_source,
            APPROVED_GRID,
        )
        total_disjoint += result.disjoint_feature_count

        print()
        print(f"Source: {result.source_id}")
        print(f"Features: {result.feature_count}")
        print(f"Covered pixels: {result.covered_pixel_count}")
        print(
            "Zero-pixel features: "
            f"{result.zero_pixel_feature_count} "
            f"{result.zero_pixel_feature_indices}"
        )
        print(
            "Partially outside features: "
            f"{result.partially_outside_feature_count} "
            f"{result.partially_outside_feature_indices}"
        )
        print(
            "Disjoint features: "
            f"{result.disjoint_feature_count} "
            f"{result.disjoint_feature_indices}"
        )

    if total_disjoint:
        print()
        print(
            "FAIL: Fully out-of-grid reference geometries "
            "were detected."
        )
        return 1

    print()
    print(
        "PASS: Real label statistics were measured and "
        "no fully out-of-grid supervision was detected."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )