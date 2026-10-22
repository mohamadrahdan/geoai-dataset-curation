"Focused tests for the release consumer, using only synthetic GeoTIFFs"
import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.training_package import ReleasedSplit, preprocess_image


def _make_release(
    tmp_path: Path,
    mask: np.ndarray,
    *,
    label_class="positive",
) -> Path:
    root = tmp_path / "versioned"

    (root / "data/images").mkdir(parents=True)
    (root / "data/masks").mkdir(parents=True)
    (root / "splits").mkdir(parents=True)

    image_path = root / "data/images/a.tif"
    mask_path = root / "data/masks/a.tif"

    raster_profile = dict(
        driver="GTiff",
        width=mask.shape[1],
        height=mask.shape[0],
        crs="EPSG:32639",
        transform=from_origin(100, 200, 10, 10),
    )

    with rasterio.open(
        image_path,
        "w",
        count=4,
        dtype="float64",
        **raster_profile,
    ) as dst:
        dst.write(
            np.full((4, *mask.shape), 2000, dtype=np.float64)
        )

    with rasterio.open(
        mask_path,
        "w",
        count=1,
        dtype="uint8",
        nodata=255,
        **raster_profile,
    ) as dst:
        dst.write(mask, 1)

    record = {
        "pair_id": "sample-id",
        "tile_id": "tile-id",
        "label_class": label_class,
        "image_path": "data/images/a.tif",
        "mask_path": "data/masks/a.tif",
    }

    (root / "splits/train.json").write_text(
        json.dumps({"split": "train", "pairs": [record]}),
        encoding="utf-8",
    )

    tracked = {
        name: "sha256:fixture"
        for name in (
            record["image_path"],
            record["mask_path"],
            "splits/train.json",
        )
    }

    manifest = {
        "schema_version": "dataset-release-manifest-v1",
        "dataset_version": "fixture_v1",
        "pair_catalog_id": "catalog-id",
        "label_values": {
            "verified_negative": 0,
            "positive": 1,
            "ignore_unlabeled": 255,
        },
        "files": tracked,
        "splits": {
            "train": {
                "path": "splits/train.json",
                "total": 1,
            }
        },
    }

    (root / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    return root


def test_release_loader_keeps_unlabeled_pixels_ignored(tmp_path):
    mask = np.array(
        [[1, 0], [255, 255]],
        dtype=np.uint8,
    )

    sample = ReleasedSplit(
        _make_release(tmp_path, mask),
        "train",
    )[0]

    assert sample["image"].shape == (4, 2, 2)
    assert sample["image"].dtype == np.float32

    np.testing.assert_array_equal(
        sample["image"],
        np.full((4, 2, 2), 0.2, dtype=np.float32),
    )

    np.testing.assert_array_equal(sample["mask"], mask)
    np.testing.assert_array_equal(
        sample["valid_mask"],
        [[True, True], [False, False]],
    )

    assert sample["pair_id"] == "sample-id"


def test_relocated_release_works(tmp_path):
    import shutil

    mask = np.array(
        [[1, 255], [0, 255]],
        dtype=np.uint8,
    )

    root = _make_release(tmp_path / "original", mask)
    destination = tmp_path / "relocated"

    shutil.copytree(root, destination)

    assert ReleasedSplit(destination, "train")[0]["mask"][0, 0] == 1


def test_unexpected_label_rejected(tmp_path):
    mask = np.array(
        [[1, 2], [0, 255]],
        dtype=np.uint8,
    )

    root = _make_release(tmp_path, mask)

    with pytest.raises(ValueError, match="Unexpected mask values"):
        ReleasedSplit(root, "train")[0]


def test_negative_only_record_cannot_have_positive_pixels(tmp_path):
    mask = np.array(
        [[1, 255], [0, 255]],
        dtype=np.uint8,
    )

    root = _make_release(
        tmp_path,
        mask,
        label_class="negative_only",
    )

    with pytest.raises(ValueError, match="Invalid negative-only mask"):
        ReleasedSplit(root, "train")[0]


def test_unknown_split_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported split"):
        ReleasedSplit(tmp_path, "training")


def test_preprocess_fails_on_bad_shape_or_nonfinite():
    with pytest.raises(ValueError, match="4 bands"):
        preprocess_image(
            np.ones((3, 2, 2), dtype=np.float64)
        )

    values = np.ones((4, 2, 2), dtype=np.float64)
    values[0, 0, 0] = np.nan

    with pytest.raises(ValueError, match="finite"):
        preprocess_image(values)


def test_untracked_path_rejected(tmp_path):
    root = _make_release(
        tmp_path,
        np.array([[1, 255], [0, 255]], dtype=np.uint8),
    )

    catalog = root / "splits/train.json"
    data = json.loads(catalog.read_text(encoding="utf-8"))

    data["pairs"][0]["image_path"] = "../../outside.tif"

    catalog.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="absent from release inventory",
    ):
        ReleasedSplit(root, "train")