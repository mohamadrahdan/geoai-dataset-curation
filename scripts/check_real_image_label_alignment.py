"Live alignment verification of the real image and label artifacts"
from pathlib import Path
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)
from geoai_dataset_curation.label_rasterization import (
    verify_raster_pair_alignment,
)


IMAGE_PATH = Path("artifacts/live/loop1/komeh_sentinel2_2024_median.tif")
LABEL_PATH = Path("artifacts/live/loop1/komeh_labels_v1.tif")


def main() -> int:
    image = inspect_raster_artifact(IMAGE_PATH)
    label = inspect_raster_artifact(LABEL_PATH)
    result = verify_raster_pair_alignment(
        image=image,
        label=label,
    )

    print("Real image-label alignment verification")
    print("=======================================")
    print(f"Image: {IMAGE_PATH}")
    print(f"Label: {LABEL_PATH}")
    print()
    print(f"CRS matches: {result.crs_matches}")
    print(f"Width matches: {result.width_matches}")
    print(f"Height matches: {result.height_matches}")
    print(
        "Transform matches: "
        f"{result.transform_matches}"
    )
    print()
    print(
        "Image shape: "
        f"{image.height} x {image.width}"
    )
    print(
        "Label shape: "
        f"{label.height} x {label.width}"
    )
    print(
        "Image transform: "
        f"{tuple(image.transform)[:6]}"
    )
    print(
        "Label transform: "
        f"{tuple(label.transform)[:6]}"
    )
    if not result.matches:
        print()
        print(
            "FAIL: Physical image and label rasters "
            "are not exactly aligned."
        )
        return 1
    print()
    print(
        "PASS: Physical image and label rasters "
        "are exactly pixel-aligned."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )