"Analyze frozen model probabilities without tuning or retraining"
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from geoai_dataset_curation.evaluation_metrics import evaluate_labeled_pixels
from geoai_dataset_curation.model_evaluation import THRESHOLD, load_frozen_model
from geoai_dataset_curation.training_package import ReleasedSplit

DEFAULT_RELEASE = Path("artifacts/releases/padena_dataset_v1.0.0")
DEFAULT_MODEL = Path("artifacts/models/padena_model_v1.0.0")
DEFAULT_REPORT = Path("artifacts/evaluations/padena_model_v1.0.0_test_v1.json")
DEFAULT_LABEL_AUDIT = Path("artifacts/diagnostics/padena_l1_15_label_audit.json")
DEFAULT_OUTPUT = Path("artifacts/diagnostics/padena_l1_15_prediction_audit.json")


def describe(values: np.ndarray) -> dict:
    if values.size == 0:
        return {"count": 0}

    return {
        "count": int(values.size),
        "min": float(np.min(values)),
        "p10": float(np.percentile(values, 10)),
        "median": float(np.median(values)),
        "p90": float(np.percentile(values, 90)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
    }


def make_edge_mask(shape: tuple[int, int], width: int = 16) -> np.ndarray:
    height, columns = shape
    if 2 * width >= min(height, columns):
        raise ValueError("Edge width is too large for this image.")

    edge = np.zeros(shape, dtype=bool)
    edge[:width, :] = True
    edge[-width:, :] = True
    edge[:, :width] = True
    edge[:, -width:] = True
    return edge


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze frozen baseline predictions.")
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--label-audit", type=Path, default=DEFAULT_LABEL_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)
    label_audit = json.loads(args.label_audit.read_text(encoding="utf-8"))

    report_sha256 = hashlib.sha256(report_bytes).hexdigest()

    if report_sha256 != label_audit["frozen_test_report_sha256"]:
        raise ValueError("Frozen test report checksum differs from the label audit.")

    if report["split"] != "test" or report["decision_threshold"] != THRESHOLD:
        raise ValueError("The frozen evaluation protocol does not match.")

    model, _, _, _ = load_frozen_model(args.model, args.release)
    dataset = ReleasedSplit(args.release, "test")

    if len(dataset) != report["tile_count"]:
        raise ValueError("Test tile count does not match the frozen report.")

    positive_scores = []
    negative_scores = []
    edge_scores = []
    interior_scores = []
    tile_results = []
    false_positive_locations = []

    for index in range(len(dataset)):
        sample = dataset[index]
        mask = sample["mask"]

        if sample["pair_id"] != report["tiles"][index]["pair_id"]:
            raise ValueError(f"Test tile identity mismatch at index {index}.")

        image = torch.from_numpy(sample["image"]).unsqueeze(0)

        with torch.inference_mode():
            logits = model(image)
            probability = torch.sigmoid(logits[0, 0]).cpu().numpy()

        if probability.shape != mask.shape or not np.isfinite(probability).all():
            raise ValueError(f"Invalid probability output at tile {index}.")

        positive = mask == 1
        negative = mask == 0
        valid = positive | negative
        predicted_positive = probability >= THRESHOLD
        predicted_positions = np.argwhere(predicted_positive)
        print(f"Tile {index:02d} predicted-positive coordinates: {predicted_positions.tolist()}")
        edge = make_edge_mask(mask.shape)

        positive_scores.append(probability[positive])
        negative_scores.append(probability[negative])
        edge_scores.append(probability[edge])
        interior_scores.append(probability[~edge])

        fp_positions = np.argwhere(predicted_positive & negative)

        for row, col in fp_positions:
            false_positive_locations.append({
                "tile_index": index,
                "row": int(row),
                "col": int(col),
                "probability": float(probability[row, col]),
            })

        tile_results.append({
            "index": index,
            "pair_id": sample["pair_id"],
            "tile_id": sample["tile_id"],
            "label_class": dataset.records[index]["label_class"],
            "valid_pixels": int(np.count_nonzero(valid)),
            "predicted_positive_pixels_all": int(np.count_nonzero(predicted_positive)),
            "predicted_positive_pixels_valid": int(np.count_nonzero(predicted_positive & valid)),
            "true_positive": int(np.count_nonzero(predicted_positive & positive)),
            "false_positive": int(len(fp_positions)),
            "false_negative": int(np.count_nonzero(~predicted_positive & positive)),
            "probability_all": describe(probability.ravel()),
            "probability_positive": describe(probability[positive]),
            "probability_negative": describe(probability[negative]),
            "probability_edge": describe(probability[edge]),
            "probability_interior": describe(probability[~edge]),
        })

    positive_values = np.concatenate(positive_scores)
    negative_values = np.concatenate(negative_scores)

    scores = np.concatenate([positive_values, negative_values])
    labels = np.concatenate([
        np.ones(positive_values.size, dtype=np.uint8),
        np.zeros(negative_values.size, dtype=np.uint8),
    ])

    metrics = evaluate_labeled_pixels(scores, labels, threshold=THRESHOLD)
    expected = report["global_metrics"]

    for key in ("tp", "tn", "fp", "fn", "valid_pixels"):
        if metrics[key] != expected[key]:
            raise ValueError(f"Frozen test result mismatch: {key}.")

    for key in ("roc_auc", "average_precision", "positive_iou", "f1"):
        observed = metrics[key]
        reference = expected[key]

        if observed is None or reference is None:
            if observed != reference:
                raise ValueError(f"Frozen test metric mismatch: {key}.")
            continue

        if not np.isclose(float(observed), float(reference), rtol=1e-9, atol=1e-12):
            raise ValueError(f"Frozen test metric mismatch: {key}.")

    result = {
        "model_version": report["model_version"],
        "dataset_version": report["dataset_version"],
        "split": "test",
        "threshold": THRESHOLD,
        "frozen_test_report_sha256": report_sha256,
        "diagnostic_edge_width_pixels": 16,
        "positive_probability": describe(positive_values),
        "negative_probability": describe(negative_values),
        "edge_probability_all_pixels": describe(np.concatenate(edge_scores)),
        "interior_probability_all_pixels": describe(np.concatenate(interior_scores)),
        "false_positive_locations": false_positive_locations,
        "tiles": tile_results,
        "note": (
            "Descriptive diagnostics only. Ignored pixels are excluded from "
            "class metrics. Edge statistics include all pixels and do not "
            "establish a causal explanation. No threshold or model tuning."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)

    print("PASS: Predictions match the frozen test evaluation.")
    print()
    print("PROBABILITY SUMMARY")
    print(f"{'Class':<18} {'Count':>9} {'Mean':>10} {'Median':>10} {'P90':>10} {'Max':>10}")

    for name, values in (
        ("Positive", result["positive_probability"]),
        ("Negative", result["negative_probability"]),
        ("Edge (all)", result["edge_probability_all_pixels"]),
        ("Interior (all)", result["interior_probability_all_pixels"]),
    ):
        print(
            f"{name:<18} {values['count']:>9} "
            f"{values['mean']:>10.5f} "
            f"{values['median']:>10.5f} "
            f"{values['p90']:>10.5f} "
            f"{values['max']:>10.5f}"
        )

    print()
    print("TEST TILE SUMMARY")
    print(f"{'Index':>5} {'Class':<15} {'MaxProb':>10} {'PredPos':>8} {'EdgeMean':>10} {'InnerMean':>10}")

    for tile in tile_results:
        print(
            f"{tile['index']:>5} "
            f"{tile['label_class']:<15} "
            f"{tile['probability_all']['max']:>10.5f} "
            f"{tile['predicted_positive_pixels_all']:>8} "
            f"{tile['probability_edge']['mean']:>10.5f} "
            f"{tile['probability_interior']['mean']:>10.5f}"
        )

    print()
    print(f"False positives on valid labels: {len(false_positive_locations)}")
    print(f"PASS: Saved diagnostic report to {args.output}")


if __name__ == "__main__":
    main()