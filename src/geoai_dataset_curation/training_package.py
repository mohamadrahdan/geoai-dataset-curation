"""Read immutable dataset releases for training without copying their rasters.
This module is framework-independent; model training belongs to L1-13.
"""
import json
from pathlib import Path, PurePosixPath
from typing import Any
import numpy as np
import rasterio

BAND_ORDER = ("B2", "B3", "B4", "B8")
REFLECTANCE_SCALE = 10000.0
LABEL_VALUES = {"verified_negative": 0, "positive": 1, "ignore_unlabeled": 255}
SUPPORTED_SPLITS = ("train", "validation", "test")


def preprocess_image(image: np.ndarray) -> np.ndarray:
    "Return four-band float32 reflectance-like inputs, without clipping"
    if image.ndim != 3 or image.shape[0] != len(BAND_ORDER):
        raise ValueError(f"Expected {len(BAND_ORDER)} bands in CHW order.")
    if not np.issubdtype(image.dtype, np.number) or not np.isfinite(image).all():
        raise ValueError("Image values must be finite and numeric.")
    return image.astype(np.float32) / REFLECTANCE_SCALE


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _release_file(root: Path, relative: str, tracked: dict[str, str]) -> Path:
    if not isinstance(relative, str) or relative not in tracked:
        raise ValueError(f"Path is absent from release inventory: {relative!r}")

    if (
        "\\" in relative
        or ":" in relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
    ):
        raise ValueError(f"Unsafe release path: {relative!r}")

    posix = PurePosixPath(relative)
    if posix.is_absolute():
        raise ValueError(f"Absolute release path: {relative!r}")

    path = root.joinpath(*posix.parts)

    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or unsafe release file: {relative!r}")

    return path


class ReleasedSplit:
    "Lazy reader for one versioned train, validation, or test split"
    def __init__(self, release_root: str | Path, split: str):
        self.root = Path(release_root)

        if split not in SUPPORTED_SPLITS:
            raise ValueError(f"Unsupported split: {split!r}")

        self.split = split
        manifest = _load_json(self.root / "manifest.json")

        if manifest.get("schema_version") != "dataset-release-manifest-v1":
            raise ValueError("Unsupported dataset release manifest schema.")

        if manifest.get("label_values") != LABEL_VALUES:
            raise ValueError("Unexpected label-value contract.")

        self.dataset_version = manifest["dataset_version"]
        self.pair_catalog_id = manifest["pair_catalog_id"]

        tracked = manifest["files"]
        summary = manifest["splits"][split]

        index = _load_json(
            _release_file(self.root, summary["path"], tracked)
        )

        if index.get("split") != split or not isinstance(index.get("pairs"), list):
            raise ValueError(f"Invalid split catalog: {split}")

        self.records = index["pairs"]

        if len(self.records) != summary["total"]:
            raise ValueError(f"Split count mismatch: {split}")

        self.samples = []

        for record in self.records:
            if record["label_class"] not in ("positive", "negative_only"):
                raise ValueError("Unexpected label class.")

            image_path = _release_file(
                self.root, record["image_path"], tracked
            )
            mask_path = _release_file(
                self.root, record["mask_path"], tracked
            )

            self.samples.append((image_path, mask_path))

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        image_path, mask_path = self.samples[index]
        record = self.records[index]

        with rasterio.open(image_path) as source, rasterio.open(mask_path) as labels:
            if source.count != 4 or labels.count != 1:
                raise ValueError(
                    f"Invalid band count for pair: {record['pair_id']}"
                )

            if source.width != labels.width or source.height != labels.height:
                raise ValueError(
                    f"Image-mask shape mismatch: {record['pair_id']}"
                )

            if source.transform != labels.transform or source.crs != labels.crs:
                raise ValueError(
                    f"Image-mask grid mismatch: {record['pair_id']}"
                )

            if labels.dtypes != ("uint8",) or labels.nodata != 255:
                raise ValueError(
                    f"Unexpected mask encoding: {record['pair_id']}"
                )

            image = preprocess_image(source.read())
            mask = labels.read(1)

        if not np.isin(mask, (0, 1, 255)).all():
            raise ValueError(
                f"Unexpected mask values: {record['pair_id']}"
            )

        if record["label_class"] == "positive" and not np.any(mask == 1):
            raise ValueError(
                f"Positive pair has no positive pixels: {record['pair_id']}"
            )

        if record["label_class"] == "negative_only" and (
            np.any(mask == 1) or not np.any(mask == 0)
        ):
            raise ValueError(
                f"Invalid negative-only mask: {record['pair_id']}"
            )

        return {
            "image": image,             # float32, shape [4, H, W]
            "mask": mask,               # uint8, values 0 / 1 / 255
            "valid_mask": mask != 255,  # bool, True for supervised pixels
            "pair_id": record["pair_id"],
            "tile_id": record["tile_id"],
        }