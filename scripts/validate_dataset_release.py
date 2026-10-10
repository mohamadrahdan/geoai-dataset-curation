"Independently validate a versioned dataset release and its portability"
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

DEFAULT_RELEASE = Path("artifacts/releases/padena_dataset_v1.0.0")
SPLITS = ("train", "validation", "test")
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict:
    require(path.is_file(), f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def resolve_release_file(release: Path, relative: str) -> Path:
    require(isinstance(relative, str), "Release path must be a string.")
    require("\\" not in relative, f"Non-portable path separator: {relative}")

    path = PurePosixPath(relative)
    require(not path.is_absolute(), f"Absolute path is forbidden: {relative}")
    require(bool(path.parts), "Empty release path.")
    require(all(part not in ("", ".", "..") for part in path.parts), f"Unsafe release path: {relative}")
    require(":" not in relative, f"Invalid release path: {relative}")

    target = release.joinpath(*path.parts)
    require(target.resolve().is_relative_to(release.resolve()), f"Path escapes release: {relative}")
    require(target.is_file(), f"Missing release file: {relative}")
    return target


def validate_release(release: Path, *, verbose: bool = True) -> dict:
    require(release.is_dir(), f"Dataset release not found: {release}")
    manifest = load_json(release / "manifest.json")

    require(manifest.get("schema_version") == "dataset-release-manifest-v1", "Unsupported manifest schema.")
    require(isinstance(manifest.get("dataset_version"), str), "Missing dataset version.")
    require(isinstance(manifest.get("pair_catalog_id"), str), "Missing pair catalog identity.")

    checksums = manifest.get("files")
    require(isinstance(checksums, dict) and bool(checksums), "Missing file checksum inventory.")
    require("manifest.json" not in checksums, "Manifest must not checksum itself.")

    actual_files = {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file()
    }
    expected_files = set(checksums) | {"manifest.json"}
    require(actual_files == expected_files, f"Release file inventory mismatch. Missing: {sorted(expected_files - actual_files)}; Extra: {sorted(actual_files - expected_files)}")

    for relative, expected_hash in checksums.items():
        require(isinstance(expected_hash, str) and SHA256_PATTERN.fullmatch(expected_hash) is not None, f"Invalid SHA256: {relative}")
        path = resolve_release_file(release, relative)
        require(path.stat().st_size > 0, f"Empty release file: {relative}")
        require(file_sha256(path) == expected_hash, f"Checksum mismatch: {relative}")

    summaries = manifest.get("splits")
    evidence = manifest.get("evidence")
    require(isinstance(summaries, dict) and set(summaries) == set(SPLITS), "Invalid split summaries.")
    require(isinstance(evidence, dict), "Missing release evidence.")
    require(set(evidence) == {"pair_qc", "visual_review", "spatial_split"}, "Incomplete release evidence.")

    for name, relative in evidence.items():
        require(relative in checksums, f"Untracked evidence: {name}")

    qc = load_json(resolve_release_file(release, evidence["pair_qc"]))
    review = load_json(resolve_release_file(release, evidence["visual_review"]))
    spatial = load_json(resolve_release_file(release, evidence["spatial_split"]))

    catalog_id = manifest["pair_catalog_id"]
    require(qc.get("pair_catalog_id") == catalog_id, "QC catalog identity mismatch.")
    require(review.get("pair_catalog_id") == catalog_id, "Review catalog identity mismatch.")
    require(spatial.get("pair_catalog_id") == catalog_id, "Spatial catalog identity mismatch.")
    require(file_sha256(resolve_release_file(release, evidence["spatial_split"])) == manifest.get("spatial_split_catalog_file_sha256"), "Spatial split evidence hash mismatch.")

    spatial_assignments = spatial.get("assignments")
    require(isinstance(spatial_assignments, list), "Invalid spatial split assignments.")

    source_assignments = {}
    for item in spatial_assignments:
        pair_id = item["pair_id"]
        require(pair_id not in source_assignments, f"Duplicate source assignment: {pair_id}")
        source_assignments[pair_id] = item

    observed_pairs = set()
    observed_tiles = set()
    observed_data_paths = set()
    group_to_split = {}
    total_pairs = 0

    if verbose:
        print("=== DATASET RELEASE VALIDATION ===")
        print(f"Version: {manifest['dataset_version']}")

    for split in SPLITS:
        summary = summaries[split]
        relative = summary["path"]
        require(relative in checksums, f"Untracked split file: {relative}")

        split_catalog = load_json(resolve_release_file(release, relative))
        require(split_catalog.get("split") == split, f"Split identity mismatch: {split}")

        records = split_catalog.get("pairs")
        require(isinstance(records, list), f"Invalid pair list: {split}")
        require(records == sorted(records, key=lambda item: item["pair_id"]), f"Non-deterministic pair ordering: {split}")

        labels = Counter()

        for item in records:
            pair_id = item["pair_id"]
            tile_id = item["tile_id"]
            group_id = item["spatial_group_id"]

            require(pair_id not in observed_pairs, f"Duplicate released pair: {pair_id}")
            require(tile_id not in observed_tiles, f"Duplicate released tile: {tile_id}")
            require(pair_id in source_assignments, f"Unknown released pair: {pair_id}")

            source = source_assignments[pair_id]
            require(source["tile_id"] == tile_id, f"Tile identity mismatch: {pair_id}")
            require(source["spatial_group_id"] == group_id, f"Spatial group mismatch: {pair_id}")
            require(source["split"] == split, f"Split assignment mismatch: {pair_id}")

            if group_id in group_to_split:
                require(group_to_split[group_id] == split, f"Spatial group crosses splits: {group_id}")
            group_to_split[group_id] = split

            require(item["label_class"] in ("positive", "negative_only"), f"Invalid label class: {pair_id}")
            labels[item["label_class"]] += 1

            for field, directory in (("image_path", "data/images/"), ("mask_path", "data/masks/")):
                data_path = item[field]
                require(data_path.startswith(directory), f"Unexpected {field}: {data_path}")
                require(data_path in checksums, f"Untracked data file: {data_path}")
                require(data_path not in observed_data_paths, f"Duplicate data file reference: {data_path}")
                resolve_release_file(release, data_path)
                observed_data_paths.add(data_path)

            observed_pairs.add(pair_id)
            observed_tiles.add(tile_id)

        observed = (len(records), labels["positive"], labels["negative_only"])
        expected = (summary["total"], summary["positive"], summary["negative_only"])
        require(observed == expected, f"{split}: summary mismatch: {observed} != {expected}")
        total_pairs += len(records)

        if verbose:
            print(f"{split}: total={observed[0]}, positive={observed[1]}, negative={observed[2]}")

    require(observed_pairs == set(source_assignments), "Released pairs do not match spatial split evidence.")
    require(total_pairs == manifest["total_pairs"], "Total pair count mismatch.")
    require(len(group_to_split) == manifest["spatial_group_count"], "Spatial group count mismatch.")
    require(len(observed_data_paths) == total_pairs * 2, "Incomplete image-mask file references.")

    expected_data_paths = {path for path in checksums if path.startswith(("data/images/", "data/masks/"))}
    require(observed_data_paths == expected_data_paths, "Unreferenced or missing data files.")

    require(manifest.get("label_values") == {
        "positive": 1,
        "verified_negative": 0,
        "ignore_unlabeled": 255,
    }, "Unexpected label-value contract.")

    result = {
        "dataset_version": manifest["dataset_version"],
        "total_pairs": total_pairs,
        "spatial_groups": len(group_to_split),
        "verified_files": len(checksums),
        "pair_catalog_id": catalog_id,
    }

    if verbose:
        print(f"Spatial groups: {result['spatial_groups']}")
        print(f"Verified files: {result['verified_files']}")
        print(f"Pair catalog ID: {catalog_id}")
        print("PASS: Dataset release validation completed.")

    return result


def check_relocation(release: Path) -> None:
    original = validate_release(release, verbose=False)

    with tempfile.TemporaryDirectory(prefix="geoai-release-relocation-") as temporary:
        relocated = Path(temporary) / "relocated_dataset"
        shutil.copytree(release, relocated)
        copied = validate_release(relocated, verbose=False)
        require(original == copied, "Relocated dataset validation differs from original.")

    print("PASS: Relocated release validated without path changes.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a versioned GeoAI dataset release.")
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE, help="Path to the dataset release directory.")
    parser.add_argument("--check-relocation", action="store_true", help="Copy release to a temporary location and revalidate.")
    args = parser.parse_args()

    validate_release(args.release)

    if args.check_relocation:
        check_relocation(args.release)


if __name__ == "__main__":
    main()
