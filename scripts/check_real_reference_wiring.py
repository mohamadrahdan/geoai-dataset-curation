"Live verification of real private reference-vector wiring"
from geoai_dataset_curation.label_rasterization import (
    load_real_reference_source_configs,
    wire_real_reference_sources,
)


TARGET_CRS = "EPSG:32639"


def main() -> int:
    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    results = wire_real_reference_sources(
        configs=configs,
        target_crs=TARGET_CRS,
    )
    print("Real reference wiring")
    print("=====================")
    print(f"Target CRS: {TARGET_CRS}")
    print(f"Sources wired: {len(results)}")
    print()
    for result in results:
        geometries = result.vector_source.geometries

        min_x = min(
            geometry.bounds[0]
            for geometry in geometries
        )
        min_y = min(
            geometry.bounds[1]
            for geometry in geometries
        )
        max_x = max(
            geometry.bounds[2]
            for geometry in geometries
        )
        max_y = max(
            geometry.bounds[3]
            for geometry in geometries
        )
        print(f"Source: {result.source_id}")
        print(
            "Supervision: "
            f"{result.vector_source.supervision.value}"
        )
        print(f"Feature count: {result.feature_count}")
        print(
            "Repaired geometries: "
            f"{result.repair_summary.repaired_count}"
        )
        print(f"Source CRS: {result.source_crs}")
        print(f"Target CRS: {result.target_crs}")
        print(
            "Projected bounds: "
            f"({min_x:.3f}, {min_y:.3f}, "
            f"{max_x:.3f}, {max_y:.3f})"
        )
        print()
    if len(results) != 3:
        print(
            "FAIL: Expected exactly three real reference sources."
        )
        return 1
    if any(
        result.feature_count <= 0
        for result in results
    ):
        print(
            "FAIL: At least one real reference source is empty."
        )
        return 1

    if any(
        result.target_crs != TARGET_CRS
        for result in results
    ):
        print(
            "FAIL: At least one source was not wired "
            "to the approved target CRS."
        )
        return 1
    print(
        "PASS: Real reference sources are validated, "
        "reprojected, and ready for rasterization."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )