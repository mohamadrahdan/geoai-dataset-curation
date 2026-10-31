"Evaluate the frozen baseline without training or checkpoint selection."
import argparse
import json
from pathlib import Path
from geoai_dataset_curation.model_evaluation import (
    THRESHOLD,
    evaluate_split,
    load_frozen_model,
)
from geoai_dataset_curation.training_package import ReleasedSplit


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the frozen Padena baseline.")
    parser.add_argument(
        "--release",
        type=Path,
        default=Path("artifacts/releases/padena_dataset_v1.0.0"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/models/padena_model_v1.0.0"),
    )
    parser.add_argument("--split", choices=("train", "validation", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm-frozen-test", action="store_true")

    args = parser.parse_args()

    # 1. Protect the frozen test split
    if args.split == "test" and not args.confirm_frozen_test:
        parser.error("Frozen test evaluation requires --confirm-frozen-test.")

    if args.split != "test" and args.confirm_frozen_test:
        parser.error("--confirm-frozen-test is only valid with --split test.")

    if args.output.exists():
        parser.error(f"Output already exists; refusing to overwrite: {args.output}")

    # 2. Verify model and dataset provenance
    model, metadata, manifest_hash, weights_hash = load_frozen_model(
        args.model,
        args.release,
    )

    # 3. Evaluate the requested split
    dataset = ReleasedSplit(args.release, args.split)
    result = evaluate_split(model, dataset)

    # 4. Build traceable evaluation report
    report = {
        "schema_version": "model-evaluation-report-v1",
        "model_version": metadata["model_version"],
        "dataset_version": dataset.dataset_version,
        "pair_catalog_id": dataset.pair_catalog_id,
        "dataset_manifest_sha256": manifest_hash,
        "model_weights_sha256": weights_hash,
        "split": args.split,
        "purpose": (
            "frozen_test_evaluation"
            if args.split == "test"
            else "development_smoke_check"
        ),
        "decision_threshold": THRESHOLD,
        "label_values": metadata["label_values"],
        "tile_count": len(dataset),
        **result,
    }

    # 5. Save without overwriting existing reports
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")

    metrics = result["global_metrics"]
    print(f"PASS: Evaluated {len(dataset)} {args.split} tiles; report: {args.output}")
    print(f"TP={metrics['tp']} TN={metrics['tn']} FP={metrics['fp']} FN={metrics['fn']}")
    print(f"Positive IoU={metrics['positive_iou']} | F1={metrics['f1']}")
    if args.split != "test":
        print("Frozen test split was NOT accessed.")
    else:
        print("Frozen test split evaluated; do not use results to tune the model.")


if __name__ == "__main__":
    main()