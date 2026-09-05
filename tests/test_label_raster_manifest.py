import json
from geoai_dataset_curation.label_rasterization import (
    LabelPixelStatisticsManifest,
    LabelRasterManifest,
    LabelSourceManifest,
    label_raster_manifest_to_dict,
    write_label_raster_manifest,
)


def make_manifest() -> LabelRasterManifest:
    return LabelRasterManifest(
        manifest_version="1.0",
        artifact_path="artifacts/labels.tif",
        output_name="labels_v1",
        crs="EPSG:32639",
        width=100,
        height=80,
        dtype="uint8",
        band_count=1,
        allowed_values=(0, 1, 255),
        grid_id="sha256:test-grid",
        image_artifact_path="artifacts/image.tif",
        image_label_alignment_verified=True,
        negative_hard_negative_overlap_pixels=3,
        pixel_statistics=LabelPixelStatisticsManifest(
            total_pixels=8000,
            supervised_pixels=300,
            positive_pixels=100,
            negative_pixels=200,
            ignore_pixels=7700,
        ),
        sources=(
            LabelSourceManifest(
                source_id="positive-reference",
                supervision="positive_reference",
                feature_count=10,
                repaired_feature_count=1,
                covered_pixel_count=100,
            ),
        ),
    )


def test_label_manifest_serializes_to_dictionary() -> None:
    result = label_raster_manifest_to_dict(
        make_manifest()
    )
    assert result["manifest_version"] == "1.0"
    assert result["allowed_values"] == (0, 1, 255)
    assert result["pixel_statistics"]["positive_pixels"] == 100
    assert result["sources"][0]["feature_count"] == 10


def test_label_manifest_writes_json(tmp_path) -> None:
    output_path = tmp_path / "labels.manifest.json"
    result = write_label_raster_manifest(
        make_manifest(),
        output_path,
    )
    loaded = json.loads(
        result.read_text(
            encoding="utf-8",
        )
    )
    assert loaded["artifact_path"] == "artifacts/labels.tif"
    assert loaded["image_label_alignment_verified"] is True
    assert loaded["sources"][0]["source_id"] == "positive-reference"