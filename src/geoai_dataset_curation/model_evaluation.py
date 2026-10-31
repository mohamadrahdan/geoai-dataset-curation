"Verify a frozen baseline and evaluate supervised pixels without training."
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol
import hashlib
import json
from typing import Any
import numpy as np
import torch
from torch import nn
from geoai_dataset_curation.baseline_model import SmallUNet
from geoai_dataset_curation.evaluation_metrics import evaluate_labeled_pixels
from geoai_dataset_curation.training_package import BAND_ORDER, REFLECTANCE_SCALE, ReleasedSplit

class EvaluationSplit(Protocol):
    @property
    def records(self) -> Sequence[Mapping[str, Any]]:
        ...

    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> Mapping[str, Any]:
        ...

THRESHOLD = 0.5


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_model(
    model_root: Path,
    release_root: Path,
) -> tuple[SmallUNet, dict[str, Any], str, str]:
    "Verify model/release provenance and load the selected checkpoint on CPU."
    metadata = json.loads((model_root / "model.json").read_text(encoding="utf-8"))
    manifest_path = release_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest_hash = _sha256(manifest_path)
    weights_path = model_root / "model.pt"
    weights_hash = _sha256(weights_path)

    # 1. Verify artifact provenance
    if metadata.get("dataset_manifest_sha256") != manifest_hash:
        raise ValueError("Dataset manifest checksum does not match model metadata.")

    if metadata.get("dataset_version") != manifest.get("dataset_version"):
        raise ValueError("Dataset version does not match model metadata.")

    if metadata.get("pair_catalog_id") != manifest.get("pair_catalog_id"):
        raise ValueError("Pair catalog does not match model metadata.")

    if metadata.get("weights_sha256") != weights_hash:
        raise ValueError("Model weights checksum does not match model metadata.")

    # 2. Verify the selected baseline configuration
    preprocessing = metadata.get("preprocessing", {})
    training = metadata.get("training", {})
    expected_labels = {"negative": 0, "positive": 1, "ignore": 255}

    if metadata.get("model_version") != "padena_model_v1.0.0":
        raise ValueError("Unexpected model version.")

    if metadata.get("architecture") != "small_unet_v1":
        raise ValueError("Unexpected model architecture.")

    if metadata.get("activation") != "leaky_relu":
        raise ValueError("The frozen baseline must use LeakyReLU.")

    if metadata.get("in_channels") != 4 or metadata.get("out_channels") != 1:
        raise ValueError("Unexpected model channel contract.")

    if metadata.get("base_channels") != 8:
        raise ValueError("Unexpected base channel count.")

    if metadata.get("label_values") != expected_labels:
        raise ValueError("Unexpected model label contract.")

    if (
        preprocessing.get("band_order") != list(BAND_ORDER)
        or preprocessing.get("scale_divisor") != REFLECTANCE_SCALE
        or preprocessing.get("clipping") is not False
        or preprocessing.get("layout") != "CHW"
    ):
        raise ValueError("Unexpected preprocessing contract.")

    if (
        training.get("epochs") != 10
        or training.get("seed") != 42
        or training.get("batch_size") != 2
        or training.get("learning_rate") != 0.001
        or training.get("loss") != "masked_bce_logits"
        or training.get("positive_class_weight", 1.0) != 1.0
        or training.get("checkpoint_policy") != "final_epoch"
    ):
        raise ValueError("Training configuration does not match the frozen baseline.")

    # 3. Load and freeze the model
    model = SmallUNet(in_channels=4, base_channels=8, activation="leaky_relu")
    model.load_state_dict(torch.load(weights_path, map_location="cpu", weights_only=True))
    model.eval()
    return model, metadata, manifest_hash, weights_hash


def evaluate_split(model: nn.Module, dataset: EvaluationSplit) -> dict[str, Any]:
    "Return global (micro) and per-tile metrics for a released split."
    if len(dataset) == 0:
        raise ValueError("Cannot evaluate an empty split.")

    model.eval()

    all_scores: list[np.ndarray] = []
    all_labels: list[np.ndarray] = []
    tiles: list[dict[str, Any]] = []

    # 4. Run inference without modifying model weights
    with torch.inference_mode():
        for index in range(len(dataset)):
            sample = dataset[index]
            image = torch.from_numpy(sample["image"]).unsqueeze(0)
            mask = sample["mask"]
            logits = model(image)

            expected_shape = (1, 1, *mask.shape)

            if tuple(logits.shape) != expected_shape or not torch.isfinite(logits).all().item():
                raise ValueError(f"Invalid predictions for pair {sample['pair_id']}.")

            probabilities = torch.sigmoid(logits[0, 0]).cpu().numpy()
            metrics = evaluate_labeled_pixels(probabilities, mask, threshold=THRESHOLD)

            tiles.append({
                "pair_id": sample["pair_id"],
                "tile_id": sample["tile_id"],
                "label_class": dataset.records[index]["label_class"],
                "metrics": metrics,
            })

            all_scores.append(probabilities.ravel())
            all_labels.append(mask.ravel())

    # 5. Calculate global metrics across all pixels
    global_metrics = evaluate_labeled_pixels(
        np.concatenate(all_scores),
        np.concatenate(all_labels),
        threshold=THRESHOLD,
    )

    # 6. Verify agreement between global and per-tile counts
    for name in ("tp", "tn", "fp", "fn", "valid_pixels", "ignored_pixels"):
        if global_metrics[name] != sum(tile["metrics"][name] for tile in tiles):
            raise RuntimeError(f"Inconsistent global and per-tile counts: {name}")

    return {
        "global_metrics": global_metrics,
        "tiles": tiles,
    }