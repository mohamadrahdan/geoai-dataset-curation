"""Read all train and validation images from the versioned dataset release.
The frozen test split is deliberately not read in this smoke check.
"""
import argparse
from pathlib import Path
import numpy as np
from geoai_dataset_curation.training_package import (
    BAND_ORDER,
    REFLECTANCE_SCALE,
    ReleasedSplit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-check versioned training inputs."
    )

    parser.add_argument(
        "--release",
        type=Path,
        default=Path(
            "artifacts/releases/padena_dataset_v1.0.0"
        ),
    )

    args = parser.parse_args()

    print(
        f"Band order: {BAND_ORDER} | "
        f"scale: {REFLECTANCE_SCALE}"
    )

    for name in ("train", "validation"):
        dataset = ReleasedSplit(args.release, name)

        positive_pairs = 0
        supervised_pixels = 0

        for i in range(len(dataset)):
            example = dataset[i]

            image = example["image"]
            mask = example["mask"]
            valid = example["valid_mask"]

            if (
                image.shape[0] != 4
                or image.shape[1:] != mask.shape
                or valid.shape != mask.shape
            ):
                raise RuntimeError(
                    f"Unexpected sample dimensions: {name}, {i}"
                )

            if (
                image.dtype != np.float32
                or not np.isfinite(image).all()
            ):
                raise RuntimeError(
                    f"Invalid normalized image: {name}, {i}"
                )

            positive_pairs += bool(np.any(mask == 1))

            supervised_pixels += int(
                np.count_nonzero(valid)
            )

        print(
            f"PASS {name}: "
            f"{len(dataset)} pairs; "
            f"{positive_pairs} positive; "
            f"{supervised_pixels} supervised pixels"
        )

    print(
        "PASS: Released dataset is readable for training. "
        "Frozen test data were not read."
    )


if __name__ == "__main__":
    main()