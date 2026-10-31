"""Synthetic and provenance checks for the frozen model evaluation runner."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from geoai_dataset_curation.baseline_model import SmallUNet
from geoai_dataset_curation.model_evaluation import evaluate_split, load_frozen_model
from geoai_dataset_curation.training_package import BAND_ORDER, REFLECTANCE_SCALE


class ToyModel(nn.Module):
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return images[:, :1]


class ToySplit:
    def __init__(self) -> None:
        self.records = [{"label_class": "positive"}, {"label_class": "negative_only"}]
        self.samples = [
            ([0.9, 0.2, 0.9, 0.4], [[1, 0], [255, 1]]),
            ([0.8, 0.1, 0.2, 0.4], [[0, 0], [255, 0]]),
        ]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict:
        probabilities, labels = self.samples[index]
        image = np.zeros((4, 2, 2), dtype=np.float32)
        image[0] = torch.logit(torch.tensor(probabilities)).reshape(2, 2).numpy()

        return {
            "image": image,
            "mask": np.array(labels, dtype=np.uint8),
            "pair_id": f"pair-{index}",
            "tile_id": f"tile-{index}",
        }


def create_artifact(tmp_path: Path) -> tuple[Path, Path]:
    release = tmp_path / "release"
    artifact = tmp_path / "model"
    release.mkdir()
    artifact.mkdir()

    manifest = {"dataset_version": "padena_dataset_v1.0.0", "pair_catalog_id": "catalog-demo"}
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    (release / "manifest.json").write_bytes(manifest_bytes)

    weights = artifact / "model.pt"
    torch.save(SmallUNet(activation="leaky_relu").state_dict(), weights)

    metadata = {
        "model_version": "padena_model_v1.0.0",
        "architecture": "small_unet_v1",
        "activation": "leaky_relu",
        "in_channels": 4,
        "out_channels": 1,
        "base_channels": 8,
        "label_values": {"negative": 0, "positive": 1, "ignore": 255},
        "preprocessing": {
            "band_order": list(BAND_ORDER),
            "scale_divisor": REFLECTANCE_SCALE,
            "clipping": False,
            "layout": "CHW",
        },
        "dataset_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "dataset_version": manifest["dataset_version"],
        "pair_catalog_id": manifest["pair_catalog_id"],
        "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
        "training": {
            "epochs": 10,
            "seed": 42,
            "batch_size": 2,
            "learning_rate": 0.001,
            "loss": "masked_bce_logits",
            "positive_class_weight": 1.0,
            "checkpoint_policy": "final_epoch",
        },
    }

    (artifact / "model.json").write_text(json.dumps(metadata), encoding="utf-8")
    return artifact, release


def test_global_counts_use_all_valid_pixels_and_ignore_255():
    result = evaluate_split(ToyModel(), ToySplit())
    global_metrics = result["global_metrics"]

    assert (
        global_metrics["tp"],
        global_metrics["tn"],
        global_metrics["fp"],
        global_metrics["fn"],
    ) == (1, 3, 1, 1)

    assert global_metrics["valid_pixels"] == 6
    assert global_metrics["ignored_pixels"] == 2
    assert global_metrics["positive_iou"] == pytest.approx(1 / 3)
    assert global_metrics["roc_auc"] == pytest.approx(0.8125)
    assert global_metrics["average_precision"] == pytest.approx(0.75)
    assert result["tiles"][1]["metrics"]["roc_auc"] is None


def test_invalid_model_output_is_rejected():
    class BadModel(nn.Module):
        def forward(self, images: torch.Tensor) -> torch.Tensor:
            return torch.zeros((1, 2, 2, 2))

    with pytest.raises(ValueError, match="Invalid predictions"):
        evaluate_split(BadModel(), ToySplit())


def test_load_frozen_model_verifies_metadata_and_weights(tmp_path):
    artifact, release = create_artifact(tmp_path)
    model, metadata, manifest_hash, weights_hash = load_frozen_model(artifact, release)

    assert not model.training
    assert metadata["activation"] == "leaky_relu"
    assert manifest_hash == metadata["dataset_manifest_sha256"]
    assert weights_hash == metadata["weights_sha256"]


def test_modified_weights_are_rejected(tmp_path):
    artifact, release = create_artifact(tmp_path)

    with (artifact / "model.pt").open("ab") as stream:
        stream.write(b"changed")

    with pytest.raises(ValueError, match="weights checksum"):
        load_frozen_model(artifact, release)


def test_modified_release_manifest_is_rejected(tmp_path):
    artifact, release = create_artifact(tmp_path)

    with (release / "manifest.json").open("ab") as stream:
        stream.write(b" ")

    with pytest.raises(ValueError, match="manifest checksum"):
        load_frozen_model(artifact, release)


def test_unconfirmed_test_split_is_blocked(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_baseline.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--split",
            "test",
            "--output",
            str(tmp_path / "report.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-frozen-test" in result.stderr
    assert not (tmp_path / "report.json").exists()