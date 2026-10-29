"Train a small segmentation baseline from the released train split only."
import argparse
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from geoai_dataset_curation.baseline_model import (
    SmallUNet,
    masked_bce_loss,
)

from geoai_dataset_curation.training_package import (
    BAND_ORDER,
    REFLECTANCE_SCALE,
    ReleasedSplit,
)


class TorchReleasedSplit(Dataset):
    "Minimal PyTorch adapter for the versioned release reader."
    def __init__(
        self,
        release: Path,
    ) -> None:
        self.source = ReleasedSplit(
            release,
            "train",
        )

    def __len__(self) -> int:
        return len(self.source)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        item = self.source[index]

        return (
            torch.from_numpy(item["image"]),
            torch.from_numpy(
                item["mask"].astype(np.int64)
            ),
        )


def count_train_labels(
    dataset: TorchReleasedSplit,
) -> tuple[int, int]:
    "Count positive and negative pixels from TRAIN only."
    positive_count = 0
    negative_count = 0

    for index in range(len(dataset)):
        mask = dataset.source[index]["mask"]

        positive_count += int(
            np.count_nonzero(mask == 1)
        )

        negative_count += int(
            np.count_nonzero(mask == 0)
        )
    return positive_count, negative_count


def main() -> None:
    # 1. Arguments
    parser = argparse.ArgumentParser(
        description=(
            "Train the initial four-band "
            "landslide segmentation baseline."
        )
    )

    parser.add_argument(
        "--release",
        type=Path,
        default=Path(
            "artifacts/releases/padena_dataset_v1.0.0"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/models/padena_model_v1.0.0"
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )

    parser.add_argument(
        "--activation",
        choices=("relu", "leaky_relu"),
        default="relu",
    )

    parser.add_argument(
        "--loss",
        choices=("masked_bce", "weighted_bce"),
        default="masked_bce",
        help=(
            "weighted_bce derives the positive class weight "
            "from TRAIN pixels only."
        ),
    )

    args = parser.parse_args()

    # 2. Validation
    if (
        args.epochs < 1
        or args.batch_size < 1
        or not (args.learning_rate > 0)
    ):
        parser.error("Epochs, batch size, and learning rate must be positive.")

    if args.output.exists():
        parser.error(
            "Output already exists; refusing to overwrite: "
            f"{args.output}"
        )

    if not (
        args.release / "manifest.json"
    ).is_file():
        parser.error("Dataset release manifest does not exist.")

    if (
        args.device == "cuda"
        and not torch.cuda.is_available()
    ):
        parser.error("CUDA was requested but is not available.")

    # 3. Device
    if args.device == "auto":
        device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
    else:
        device = torch.device(args.device)

    # 4. Reproducibility
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

    # 5. Training data
    dataset = TorchReleasedSplit(args.release)

    if len(dataset) == 0:
        parser.error("Training split is empty.")

    # 6. Optional class weighting
    positive_count = None
    negative_count = None
    positive_weight = 1.0

    if args.loss == "weighted_bce":

        positive_count, negative_count = count_train_labels(
            dataset
        )

        if positive_count == 0 or negative_count == 0:
            parser.error("Weighted BCE requires both labeled classes in TRAIN.")

        positive_weight = (
            negative_count / positive_count
        )

        print(
            "TRAIN-only class counts: "
            f"positive={positive_count}, "
            f"negative={negative_count} "
            f"| pos_weight={positive_weight:.6f}"
        )

    # 7. DataLoader
    generator = torch.Generator().manual_seed(
        args.seed
    )

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        generator=generator,
    )

    # 8. Model and optimizer
    model = SmallUNet(
        in_channels=4,
        base_channels=8,
        activation=args.activation,
    ).to(device)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.learning_rate,
    )

    history: list[float] = []

    print(
        f"Dataset: {dataset.source.dataset_version} "
        f"| train pairs: {len(dataset)} "
        f"| device: {device} "
        f"| activation: {args.activation} "
        f"| loss: {args.loss}"
    )

    print(
        "Checkpoint policy: final epoch only "
        "(no validation-based selection)."
    )

    # 9. Training loop
    for epoch in range(
        1,
        args.epochs + 1,
    ):

        model.train()

        weighted_loss_sum = 0.0
        supervised_count = 0

        for images, masks in loader:

            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad(
                set_to_none=True
            )

            logits = model(images)

            loss = masked_bce_loss(
                logits,
                masks,
                pos_weight=positive_weight,
            )

            loss.backward()
            optimizer.step()

            n_valid = int(
                (masks != 255).sum().item()
            )

            weighted_loss_sum += (
                float(loss.item()) * n_valid
            )

            supervised_count += n_valid

        epoch_loss = (
            weighted_loss_sum / supervised_count
        )

        history.append(epoch_loss)

        print(
            f"epoch={epoch:02d}/{args.epochs} "
            f"train_{args.loss}={epoch_loss:.6f}",
            flush=True,
        )

    # 10. Metadata
    manifest_bytes = (
        args.release / "manifest.json"
    ).read_bytes()

    config = {
        "model_version": "padena_model_v1.0.0",
        "architecture": "small_unet_v1",
        "activation": args.activation,
        "base_channels": 8,
        "in_channels": 4,
        "out_channels": 1,
        "dataset_version": dataset.source.dataset_version,
        "dataset_manifest_sha256": hashlib.sha256(
            manifest_bytes
        ).hexdigest(),
        "pair_catalog_id": dataset.source.pair_catalog_id,
        "preprocessing": {
            "band_order": list(BAND_ORDER),
            "scale_divisor": REFLECTANCE_SCALE,
            "clipping": False,
            "layout": "CHW",
        },
        "label_values": {
            "negative": 0,
            "positive": 1,
            "ignore": 255,
        },
        "training": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "seed": args.seed,
            "loss": (
                "class_weighted_masked_bce_logits"
                if args.loss == "weighted_bce"
                else "masked_bce_logits"
            ),
            "positive_class_weight": positive_weight,
            "class_weight_source": (
                "train"
                if args.loss == "weighted_bce"
                else None
            ),
            "train_positive_pixels": positive_count,
            "train_negative_pixels": negative_count,
            "checkpoint_policy": "final_epoch",
            "device": str(device),
            "torch_version": str(torch.__version__),
        },
        "train_loss_by_epoch": history,
        "evaluation_status": "not_evaluated",
    }

    # 11. Save weights and metadata
    args.output.mkdir(
        parents=True,
        exist_ok=False,
    )

    weights_path = (
        args.output / "model.pt"
    )

    torch.save(
        model.cpu().state_dict(),
        weights_path,
    )

    config["weights_sha256"] = hashlib.sha256(
        weights_path.read_bytes()
    ).hexdigest()

    metadata_path = (
        args.output / "model.json"
    )

    metadata_path.write_text(
        json.dumps(
            config,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    # 12. Reload saved model
    reloaded = SmallUNet(
        in_channels=config["in_channels"],
        base_channels=config["base_channels"],
        activation=config["activation"],
    )

    reloaded.load_state_dict(
        torch.load(
            weights_path,
            map_location="cpu",
            weights_only=True,
        )
    )

    reloaded.eval()

    # 13. Reload verification with TRAIN data only
    with torch.inference_mode():

        sample, _ = dataset[0]

        logits = reloaded(
            sample.unsqueeze(0)
        )

        expected_shape = (
            1,
            1,
            *sample.shape[-2:],
        )

        if (
            logits.shape != expected_shape
            or not torch.isfinite(logits).all()
        ):
            raise RuntimeError(
                "Reloaded model produced an invalid output."
            )

    print(
        f"PASS: Saved and reloaded {weights_path} "
        f"| prediction shape: {tuple(logits.shape)}"
    )

    print(
        "NOTE: Training completed; "
        "model performance has NOT been evaluated."
    )


if __name__ == "__main__":
    main()