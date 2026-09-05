"Persistent manifest for a real label-raster artifact"
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LabelSourceManifest:
    "Recorded contribution of one reference source"
    source_id: str
    supervision: str
    feature_count: int
    repaired_feature_count: int
    covered_pixel_count: int


@dataclass(frozen=True)
class LabelPixelStatisticsManifest:
    "Recorded pixel distribution of the final label raster"
    total_pixels: int
    supervised_pixels: int
    positive_pixels: int
    negative_pixels: int
    ignore_pixels: int


@dataclass(frozen=True)
class LabelRasterManifest:
    "Persistent provenance record for one label-raster artifact"
    manifest_version: str
    artifact_path: str
    output_name: str
    crs: str
    width: int
    height: int
    dtype: str
    band_count: int
    allowed_values: tuple[int, ...]
    grid_id: str
    image_artifact_path: str
    image_label_alignment_verified: bool
    negative_hard_negative_overlap_pixels: int
    pixel_statistics: LabelPixelStatisticsManifest
    sources: tuple[LabelSourceManifest, ...]


def label_raster_manifest_to_dict(
    manifest: LabelRasterManifest,
) -> dict[str, Any]:
    "Convert the manifest into a JSON-serializable dictionary"
    return asdict(manifest)


def write_label_raster_manifest(
    manifest: LabelRasterManifest,
    output_path: Path,
) -> Path:
    "Serialize a label-raster manifest as formatted JSON"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        json.dumps(
            label_raster_manifest_to_dict(manifest),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path