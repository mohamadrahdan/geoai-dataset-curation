
"""Compare spatially independent split options on real Komeh catalogs."""
import json
from collections import Counter
from itertools import permutations
from pathlib import Path

ROOT = Path("artifacts/live/loop1")
TILES_PATH = ROOT / "komeh_candidate_tiles_v1.catalog.json"
PAIRS_PATH = ROOT / "komeh_image_mask_pairs_v1.catalog.json"

SPLITS = ("train", "validation", "test")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def connected(first, second):
    """Match the current zero-gap spatial grouping policy."""
    row_gap = max(
        first["row_offset_pixels"]
        - (second["row_offset_pixels"] + second["read_height_pixels"]),
        second["row_offset_pixels"]
        - (first["row_offset_pixels"] + first["read_height_pixels"]),
        0,
    )
    col_gap = max(
        first["column_offset_pixels"]
        - (second["column_offset_pixels"] + second["read_width_pixels"]),
        second["column_offset_pixels"]
        - (first["column_offset_pixels"] + first["read_width_pixels"]),
        0,
    )
    return row_gap == 0 and col_gap == 0


def build_components(pairs, tiles):
    parent = list(range(len(pairs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            if connected(
                tiles[pairs[i]["tile_id"]],
                tiles[pairs[j]["tile_id"]],
            ):
                root_i = find(i)
                root_j = find(j)
                if root_i != root_j:
                    parent[root_j] = root_i

    components = {}
    for i, pair in enumerate(pairs):
        components.setdefault(find(i), []).append(pair)

    return sorted(
        components.values(),
        key=lambda group: (-len(group), group[0]["pair_id"]),
    )


def counts(group):
    labels = Counter(pair["label_class"] for pair in group)
    return (
        len(group),
        labels["positive"],
        labels["negative_only"],
    )


def main():
    tile_catalog = load_json(TILES_PATH)
    pair_catalog = load_json(PAIRS_PATH)

    tiles = {
        tile["tile_id"]: tile
        for tile in tile_catalog["tiles"]
    }
    pairs = pair_catalog["pairs"]

    assert len(pairs) == 50
    assert len({p["pair_id"] for p in pairs}) == len(pairs)
    assert len({p["tile_id"] for p in pairs}) == len(pairs)
    assert all(p["tile_id"] in tiles for p in pairs)
    assert all(
        p["label_class"] in ("positive", "negative_only")
        for p in pairs
    )

    groups = build_components(pairs, tiles)

    print("=== REAL SPATIAL GROUPS ===")
    for i, group in enumerate(groups, 1):
        total, positive, negative = counts(group)
        print(
            f"Group {i}: total={total}, "
            f"positive={positive}, negative={negative}"
        )

    print(f"\nIndependent groups: {len(groups)}")
    print(f"Total pairs: {sum(len(g) for g in groups)}")

    if len(groups) != 3:
        raise RuntimeError(
            "Expected three groups; investigate before assignment."
        )

    print("\n=== ALL THREE-WAY ASSIGNMENTS ===")
    for order in permutations(range(3)):
        result = {
            split: counts(groups[group_index])
            for split, group_index in zip(SPLITS, order)
        }
        print(
            " | ".join(
                f"{split}: {result[split]}"
                for split in SPLITS
            )
        )

    print("\nPASS: Diagnostic spatial-group analysis completed.")
    print("No split policy has been finalized.")


def audit_persisted_split():
    split_path = ROOT / "komeh_spatial_split_v1.catalog.json"
    catalog = load_json(split_path)
    tile_catalog = load_json(TILES_PATH)

    tiles = {tile["tile_id"]: tile for tile in tile_catalog["tiles"]}
    assignments = catalog["assignments"]

    assert len(assignments) == 50
    assert len({item["pair_id"] for item in assignments}) == 50

    violations = []
    for i, first in enumerate(assignments):
        for second in assignments[i + 1:]:
            if first["split"] == second["split"]:
                continue
            if connected(tiles[first["tile_id"]], tiles[second["tile_id"]]):
                violations.append((first["pair_id"], second["pair_id"]))

    if violations:
        raise RuntimeError(f"Spatial leakage detected: {len(violations)} violations.")

    print(f"Audited assignments: {len(assignments)}")
    print("Cross-split spatial leakage violations: 0")
    print("PASS: Independent spatial leakage audit.")


if __name__ == "__main__":
    main()
    audit_persisted_split()
