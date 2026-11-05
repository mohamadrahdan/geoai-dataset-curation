"Audit label coverage in the released Padena dataset"
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from geoai_dataset_curation.training_package import ReleasedSplit

DEFAULT_RELEASE = Path("artifacts/releases/padena_dataset_v1.0.0")
DEFAULT_REPORT = Path("artifacts/evaluations/padena_model_v1.0.0_test_v1.json")
DEFAULT_OUTPUT = Path("artifacts/diagnostics/padena_l1_15_label_audit.json")


def percentage(part: int, total: int) -> float | None:
    return round(100.0 * part / total, 4) if total else None


def audit_split(release: Path, split: str) -> dict:
    dataset = ReleasedSplit(release, split)
    totals = {"positive": 0, "negative": 0, "ignored": 0}
    tiles = []

    for index in range(len(dataset)):
        sample = dataset[index]
        mask = sample["mask"]
        if not np.isin(mask, (0, 1, 255)).all():
            raise ValueError(f"Unexpected mask values in {split} tile {index}.")

        positive = int(np.count_nonzero(mask == 1))
        negative = int(np.count_nonzero(mask == 0))
        ignored = int(np.count_nonzero(mask == 255))
        valid = positive + negative
        total = valid + ignored

        totals["positive"] += positive
        totals["negative"] += negative
        totals["ignored"] += ignored

        tiles.append({
            "index": index,
            "tile_id": sample["tile_id"],
            "pair_id": sample["pair_id"],
            "label_class": dataset.records[index]["label_class"],
            "positive_pixels": positive,
            "negative_pixels": negative,
            "ignored_pixels": ignored,
            "valid_pixels": valid,
            "positive_prevalence_pct": percentage(positive, valid),
            "ignored_pct": percentage(ignored, total),
        })

    positive = totals["positive"]
    negative = totals["negative"]
    ignored = totals["ignored"]
    valid = positive + negative

    return {
        "split": split,
        "tile_count": len(dataset),
        "positive_tiles": sum(t["positive_pixels"] > 0 for t in tiles),
        "negative_only_tiles": sum(
            t["positive_pixels"] == 0 and t["negative_pixels"] > 0 for t in tiles
        ),
        "positive_pixels": positive,
        "negative_pixels": negative,
        "ignored_pixels": ignored,
        "valid_pixels": valid,
        "positive_prevalence_pct": percentage(positive, valid),
        "ignored_pct": percentage(ignored, valid + ignored),
        "tiles": tiles,
    }


def verify_test_counts(audit: dict, report: dict) -> None:
    if report["split"] != "test":
        raise ValueError("The evaluation report must belong to the test split.")
    if report["tile_count"] != audit["tile_count"]:
        raise ValueError("Test tile count does not match the frozen report.")
    metrics = report["global_metrics"]

    fields = {
        "positive_pixels": "positive_pixels",
        "negative_pixels": "negative_pixels",
        "ignored_pixels": "ignored_pixels",
        "valid_pixels": "valid_pixels",
    }

    for audit_key, metric_key in fields.items():
        if audit[audit_key] != metrics[metric_key]:
            raise ValueError(f"Test mismatch: {audit_key}.")

    print("PASS: Label counts match the frozen test evaluation report.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit released dataset labels.")
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)

    audits = {
        split: audit_split(args.release, split)
        for split in ("train", "validation", "test")
    }

    verify_test_counts(audits["test"], report)

    result = {
        "dataset_version": report["dataset_version"],
        "model_version": report["model_version"],
        "frozen_test_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "splits": audits,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)

    print()
    print("SPLIT SUMMARY")
    print(f"{'Split':<12} {'Tiles':>6} {'PosTiles':>9} {'Positive':>10} {'Negative':>10} {'Valid%':>9} {'Pos/Valid%':>11}")

    for split, data in audits.items():
        valid_pct = 100.0 - data["ignored_pct"]

        print(
            f"{split:<12} {data['tile_count']:>6} "
            f"{data['positive_tiles']:>9} "
            f"{data['positive_pixels']:>10} "
            f"{data['negative_pixels']:>10} "
            f"{valid_pct:>9.2f} "
            f"{data['positive_prevalence_pct']:>11.2f}"
        )

    print()
    print("TEST TILE DETAILS")
    print(f"{'Index':>5} {'Class':<17} {'Positive':>9} {'Negative':>9} {'Ignored%':>9}")

    for tile in audits["test"]["tiles"]:
        print(
            f"{tile['index']:>5} "
            f"{tile['label_class']:<17} "
            f"{tile['positive_pixels']:>9} "
            f"{tile['negative_pixels']:>9} "
            f"{tile['ignored_pct']:>9.2f}"
        )

    print()
    print(f"PASS: Saved diagnostic report to {args.output}")


if __name__ == "__main__":
    main()