"Build the first versioned dataset release from verified Loop 1 artifacts"
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("artifacts/live/loop1")
RELEASES_ROOT = Path("artifacts/releases")
VERSION = "padena_dataset_v1.0.0"
OUTPUT_PATH = RELEASES_ROOT / VERSION

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
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_release(destination: Path) -> dict:
    pair_catalog = load_json(PAIR_PATH)
    qc_report = load_json(QC_PATH)
    review_catalog = load_json(REVIEW_PATH)
    split_catalog = load_json(SPLIT_PATH)

    pairs = pair_catalog["pairs"]
    assignments = split_catalog["assignments"]
    pair_id = pair_catalog["pair_catalog_id"]

    require(len(pairs) == 50 and len(assignments) == 50, "Expected 50 pairs and 50 assignments.")
    require(qc_report["pair_catalog_id"] == pair_id, "QC provenance mismatch.")
    require(review_catalog["pair_catalog_id"] == pair_id, "Visual review provenance mismatch.")
    require(split_catalog["pair_catalog_id"] == pair_id, "Spatial split provenance mismatch.")

    pair_by_id = {pair["pair_id"]: pair for pair in pairs}
    assignment_by_id = {item["pair_id"]: item for item in assignments}

    require(len(pair_by_id) == 50 and len(assignment_by_id) == 50, "Duplicate pair IDs detected.")
    require(set(pair_by_id) == set(assignment_by_id), "Missing or extra split assignments.")
    require(len({pair["tile_id"] for pair in pairs}) == 50, "Duplicate tile IDs detected.")
    require(len({item["tile_id"] for item in assignments}) == 50, "Duplicate assigned tile IDs detected.")

    group_splits = {}
    split_records = {name: [] for name in EXPECTED_COUNTS}
    file_checksums = {}

    for pair in pairs:
        assignment = assignment_by_id[pair["pair_id"]]
        split = assignment["split"]
        group_id = assignment["spatial_group_id"]

        require(split in split_records, f"Unexpected split: {split}")
        require(assignment["tile_id"] == pair["tile_id"], "Pair/tile identity mismatch.")

        if group_id in group_splits:
            require(group_splits[group_id] == split, "Spatial group divided across splits.")
        group_splits[group_id] = split

        filename = pair["tile_id"].removeprefix("sha256:") + ".tif"
        image_source = Path(pair["image_tile_path"])
        mask_source = Path(pair["mask_tile_path"])

        require(image_source.is_file(), f"Missing image: {image_source}")
        require(mask_source.is_file(), f"Missing mask: {mask_source}")
        require(image_source.stat().st_size > 0, f"Empty image: {image_source}")
        require(mask_source.stat().st_size > 0, f"Empty mask: {mask_source}")

        image_relative = Path("data/images") / filename
        mask_relative = Path("data/masks") / filename
        image_target = destination / image_relative
        mask_target = destination / mask_relative

        require(not image_target.exists() and not mask_target.exists(), "Duplicate release file destination.")

        image_target.parent.mkdir(parents=True, exist_ok=True)
        mask_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image_source, image_target)
        shutil.copyfile(mask_source, mask_target)

        image_hash = file_sha256(image_target)
        mask_hash = file_sha256(mask_target)

        require(image_hash == file_sha256(image_source), "Image checksum mismatch after copying.")
        require(mask_hash == file_sha256(mask_source), "Mask checksum mismatch after copying.")

        file_checksums[image_relative.as_posix()] = image_hash
        file_checksums[mask_relative.as_posix()] = mask_hash
        split_records[split].append({
            "pair_id": pair["pair_id"],
            "tile_id": pair["tile_id"],
            "spatial_group_id": group_id,
            "label_class": pair["label_class"],
            "image_path": image_relative.as_posix(),
            "mask_path": mask_relative.as_posix(),
        })

    require(len(group_splits) == 3, "Expected three independent spatial groups.")
    split_summaries = {}
    for split, expected in EXPECTED_COUNTS.items():
        records = sorted(split_records[split], key=lambda item: item["pair_id"])
        counts = Counter(record["label_class"] for record in records)
        observed = (len(records), counts["positive"], counts["negative_only"])
        require(observed == expected, f"Unexpected {split} distribution: {observed}")

        relative = Path("splits") / f"{split}.json"
        write_json(destination / relative, {"split": split, "pairs": records})
        file_checksums[relative.as_posix()] = file_sha256(destination / relative)

        split_summaries[split] = {
            "path": relative.as_posix(),
            "total": observed[0],
            "positive": observed[1],
            "negative_only": observed[2],
        }

    evidence_sources = {
        "pair_qc": QC_PATH,
        "visual_review": REVIEW_PATH,
        "spatial_split": SPLIT_PATH,
    }
    evidence = {}

    for name, source in evidence_sources.items():
        relative = Path("evidence") / f"{name}.json"
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        file_checksums[relative.as_posix()] = file_sha256(target)
        evidence[name] = relative.as_posix()

    manifest = {
        "schema_version": "dataset-release-manifest-v1",
        "dataset_version": VERSION,
        "study_area": "Komeh, Padena, Isfahan",
        "pair_catalog_id": pair_id,
        "spatial_split_catalog_file_sha256": file_checksums[evidence["spatial_split"]],
        "total_pairs": 50,
        "spatial_group_count": len(group_splits),
        "splits": split_summaries,
        "evidence": evidence,
        "files": dict(sorted(file_checksums.items())),
        "label_values": {
            "positive": 1,
            "verified_negative": 0,
            "ignore_unlabeled": 255,
        },
        "limitations": [
            "Only three spatial groups are available.",
            "The validation split contains no positive samples.",
            "The geometric leakage audit does not establish full statistical independence.",
            "The frozen test set must not be used for training or model selection.",
        ],
    }

    write_json(destination / "manifest.json", manifest)
    return manifest


def main() -> None:
    if OUTPUT_PATH.exists():
        raise RuntimeError(f"Release already exists; refusing to overwrite: {OUTPUT_PATH}")

    RELEASES_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{VERSION}-", dir=RELEASES_ROOT) as temporary:
        temporary_path = Path(temporary)
        manifest = build_release(temporary_path)

        for relative, expected_hash in manifest["files"].items():
            path = temporary_path / relative
            require(path.is_file(), f"Missing release file: {relative}")
            require(file_sha256(path) == expected_hash, f"Checksum mismatch: {relative}")

        temporary_path.rename(OUTPUT_PATH)

    print("=== DATASET RELEASE ===")
    print(f"Version: {VERSION}")
    print(f"Total pairs: {manifest['total_pairs']}")
    print(f"Spatial groups: {manifest['spatial_group_count']}")

    for split, counts in manifest["splits"].items():
        print(f"{split}: total={counts['total']}, positive={counts['positive']}, negative={counts['negative_only']}")

    print(f"Verified release files: {len(manifest['files'])}")
    print(f"Output: {OUTPUT_PATH}")
    print("PASS: Dataset release built successfully.")


if __name__ == "__main__":
    main()
