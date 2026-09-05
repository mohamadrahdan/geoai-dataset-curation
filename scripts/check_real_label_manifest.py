"Generate and validate the persistent real Loop 1 label manifest"
import json
from pathlib import Path
from geoai_dataset_curation.label_rasterization import (
    LabelPixelStatisticsManifest,
    LabelRasterManifest,
    LabelSourceManifest,
    write_label_raster_manifest,
)


LABEL_ARTIFACT_PATH = ("artifacts/live/loop1/komeh_labels_v1.tif")

IMAGE_ARTIFACT_PATH = ("artifacts/live/loop1/komeh_sentinel2_2024_median.tif")

MANIFEST_PATH = Path("artifacts/live/loop1/komeh_labels_v1.manifest.json")

GRID_ID = (
    "sha256:"
    "d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799"
)


def main() -> int:
    manifest = LabelRasterManifest(
        manifest_version="1.0",
        artifact_path=LABEL_ARTIFACT_PATH,
        output_name="komeh_labels_v1",
        crs="EPSG:32639",
        width=5712,
        height=5493,
        dtype="uint8",
        band_count=1,
        allowed_values=(0, 1, 255),
        grid_id=GRID_ID,
        image_artifact_path=IMAGE_ARTIFACT_PATH,
        image_label_alignment_verified=True,
        negative_hard_negative_overlap_pixels=3,
        pixel_statistics=LabelPixelStatisticsManifest(
            total_pixels=31_376_016,
            supervised_pixels=82_321,
            positive_pixels=17_933,
            negative_pixels=64_388,
            ignore_pixels=31_293_695,
        ),
        sources=(
            LabelSourceManifest(
                source_id="landslide-reference",
                supervision="positive_reference",
                feature_count=57,
                repaired_feature_count=1,
                covered_pixel_count=17_933,
            ),
            LabelSourceManifest(
                source_id="negative-reference",
                supervision="negative_reference",
                feature_count=54,
                repaired_feature_count=1,
                covered_pixel_count=23_640,
            ),
            LabelSourceManifest(
                source_id="hard-negative-reference",
                supervision="hard_negative_reference",
                feature_count=49,
                repaired_feature_count=0,
                covered_pixel_count=40_751,
            ),
        ),
    )
    write_label_raster_manifest(
        manifest,
        MANIFEST_PATH,
    )
    loaded = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )

    checks = {
        "manifest_version": loaded["manifest_version"] == "1.0",
        "grid_id": loaded["grid_id"] == GRID_ID,
        "artifact_path": loaded["artifact_path"] == LABEL_ARTIFACT_PATH,
        "alignment": loaded["image_label_alignment_verified"] is True,
        "allowed_values": loaded["allowed_values"] == [0, 1, 255],
        "source_count": len(loaded["sources"]) == 3,
        "feature_count": sum(
            source["feature_count"]
            for source in loaded["sources"]
        )
        == 160,
        "pixel_total": loaded["pixel_statistics"]["total_pixels"]
        == 31_376_016,
        "supervised_pixels":
            loaded["pixel_statistics"]["supervised_pixels"]
            == 82_321,
    }
    print("Real label manifest")
    print("===================")
    print(f"Path: {MANIFEST_PATH}")
    print()

    for name, passed in checks.items():
        print(f"{name}: {passed}")
    if not all(checks.values()):
        print()
        print("FAIL: Real label manifest validation failed.")
        return 1

    print()
    print(
        "PASS: Real label manifest was written and "
        "validated successfully."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )