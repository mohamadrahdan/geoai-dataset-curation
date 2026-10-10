"Check whether real Loop 1 artifacts are ready for dataset release."
import json
from collections import Counter
from pathlib import Path

ROOT = Path("artifacts/live/loop1")
PAIR_PATH = ROOT / "komeh_image_mask_pairs_v1.catalog.json"
QC_PATH = ROOT / "komeh_image_mask_pairs_v1.qc.json"
REVIEW_PATH = ROOT / "komeh_image_mask_pairs_v1.visual_review.json"
SPLIT_PATH = ROOT / "komeh_spatial_split_v1.catalog.json"

EXPECTED_COUNTS = {
    "train": (33, 8, 25),
    "validation": (4, 0, 4),
    "test": (13, 11, 2),
}


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Missing release input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    pair_catalog = load_json(PAIR_PATH)
    qc_report = load_json(QC_PATH)
    review_catalog = load_json(REVIEW_PATH)
    split_catalog = load_json(SPLIT_PATH)

    pairs = pair_catalog["pairs"]
    assignments = split_catalog["assignments"]
    pair_catalog_id = pair_catalog["pair_catalog_id"]

    require(len(pairs) == 50, "Expected 50 image-mask pairs.")
    require(len(assignments) == 50, "Expected 50 split assignments.")

    pair_ids = [pair["pair_id"] for pair in pairs]
    tile_ids = [pair["tile_id"] for pair in pairs]

    require(len(set(pair_ids)) == 50, "Duplicate pair IDs detected.")
    require(len(set(tile_ids)) == 50, "Duplicate tile IDs detected.")

    require(qc_report["pair_catalog_id"] == pair_catalog_id, "QC pair catalog ID mismatch.")
    require(review_catalog["pair_catalog_id"] == pair_catalog_id, "Visual review pair catalog ID mismatch.")
    require(split_catalog["pair_catalog_id"] == pair_catalog_id, "Split pair catalog ID mismatch.")

    pair_by_id = {pair["pair_id"]: pair for pair in pairs}
    assignment_by_id = {item["pair_id"]: item for item in assignments}

    require(len(assignment_by_id) == 50, "Duplicate split assignments detected.")
    require(set(assignment_by_id) == set(pair_by_id), "Split assignments do not cover all pairs.")

    for pair in pairs:
        for field in ("image_tile_path", "mask_tile_path"):
            path = Path(pair[field])
            require(path.is_file(), f"Missing physical artifact: {path}")
            require(path.stat().st_size > 0, f"Empty physical artifact: {path}")

        assignment = assignment_by_id[pair["pair_id"]]
        require(assignment["tile_id"] == pair["tile_id"], "Pair-to-tile assignment mismatch.")

    reviews = review_catalog["reviews"]
    require(len(reviews) == 50, "Expected 50 human reviews.")
    require(len({item["pair_id"] for item in reviews}) == 50, "Duplicate human reviews detected.")
    require({item["pair_id"] for item in reviews} == set(pair_ids), "Human reviews do not cover all pairs.")
    require(all(item["status"] == "pass" for item in reviews), "Human review includes non-passing results.")

    groups = {}
    for assignment in assignments:
        group_id = assignment["spatial_group_id"]
        split = assignment["split"]
        require(split in EXPECTED_COUNTS, f"Unexpected split: {split}")
        if group_id in groups:
            require(groups[group_id] == split, "A spatial group was divided across splits.")
        groups[group_id] = split

    require(len(groups) == 3, "Expected exactly three spatial groups.")

    print("=== DATASET RELEASE INPUT CHECK ===")

    for split, expected in EXPECTED_COUNTS.items():
        selected = [item for item in assignments if item["split"] == split]
        labels = Counter(pair_by_id[item["pair_id"]]["label_class"] for item in selected)
        observed = (len(selected), labels["positive"], labels["negative_only"])
        require(observed == expected, f"{split}: expected {expected}, found {observed}")
        print(f"{split}: total={observed[0]}, positive={observed[1]}, negative={observed[2]}")

    print(f"Physical image files: {len(pairs)}")
    print(f"Physical mask files: {len(pairs)}")
    print(f"Human reviews passed: {len(reviews)}")
    print(f"Spatial groups: {len(groups)}")
    print(f"Pair catalog ID: {pair_catalog_id}")
    print("PASS: Dataset release inputs are ready.")


if __name__ == "__main__":
    main()
