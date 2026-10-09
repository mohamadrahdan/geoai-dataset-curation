
"""Build the real Loop 1 spatial split from verified Komeh artifacts."""
import json
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from geoai_dataset_curation.quality_control.artifact_loading import (
    load_pair_qc_input_artifacts,
)
from geoai_dataset_curation.quality_control.report import (
    pair_qc_report_to_dict,
    run_pair_quality_control,
)
from geoai_dataset_curation.quality_control.visual_review_io import (
    read_visual_review_catalog,
)
from geoai_dataset_curation.spatial_split import (
    SpatialAssignmentPolicy,
    SpatialDistanceMetric,
    SpatialGroupingPolicy,
    SpatialSplitName,
    accept_spatial_split_inputs,
    build_spatial_leakage_group_catalog,
    build_spatial_relationship_catalog,
    build_spatial_split_catalog,
    validate_spatial_split_catalog,
)


ROOT = Path("artifacts/live/loop1")

TILE_PATH = ROOT / "komeh_candidate_tiles_v1.catalog.json"
SELECTION_PATH = ROOT / "komeh_sampling_selection_v1.catalog.json"
PROVENANCE_PATH = ROOT / "komeh_tile_negative_provenance_v1.catalog.json"
PAIR_PATH = ROOT / "komeh_image_mask_pairs_v1.catalog.json"
QC_PATH = ROOT / "komeh_image_mask_pairs_v1.qc.json"
REVIEW_PATH = ROOT / "komeh_image_mask_pairs_v1.visual_review.json"

OUTPUT_PATH = ROOT / "komeh_spatial_split_v1.catalog.json"

# Loop 1 baseline: explicit and documented, not a general optimum.
GROUPING_POLICY = SpatialGroupingPolicy(
    distance_metric=SpatialDistanceMetric.EUCLIDEAN_PIXEL_GAP,
    maximum_gap_pixels=0,
)

ASSIGNMENT_POLICY = SpatialAssignmentPolicy(
    train_fraction=0.6,
    validation_fraction=0.2,
    test_fraction=0.2,
    seed=42,
)


def canonical_json(payload):
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def main():
    # 1. Load validated upstream artifacts.
    inputs = load_pair_qc_input_artifacts(
        tile_catalog_path=TILE_PATH,
        selection_path=SELECTION_PATH,
        provenance_path=PROVENANCE_PATH,
        pair_catalog_path=PAIR_PATH,
    )
    pairs = inputs.pair_catalog

    # 2. Independently rerun automated QC against physical files.
    qc_report = run_pair_quality_control(
        pairs,
        tile_catalog=inputs.tile_catalog,
        selection=inputs.selection,
        provenance=inputs.provenance,
        expected_image_band_count=4,
        expected_image_dtype="float64",
    )

    # Verify the previously persisted automated QC evidence.
    saved_qc = json.loads(QC_PATH.read_text(encoding="utf-8"))
    if saved_qc != pair_qc_report_to_dict(qc_report):
        raise RuntimeError(
            "Persisted QC report differs from current QC results."
        )

    # 3. Require completed human review.
    review = read_visual_review_catalog(
        REVIEW_PATH,
        pair_catalog=pairs,
        require_complete=True,
    )

    acceptance = accept_spatial_split_inputs(
        pairs,
        qc_report=qc_report,
        visual_review_catalog=review,
    )

    # 4. Generate relationships using the official implementation.
    relationships = build_spatial_relationship_catalog(
        acceptance,
        pair_catalog=pairs,
        tile_catalog=inputs.tile_catalog,
        policy=GROUPING_POLICY,
        output_name="komeh_spatial_relationships_v1",
    )

    groups = build_spatial_leakage_group_catalog(
        relationships,
        policy=GROUPING_POLICY,
        output_name="komeh_spatial_groups_v1",
    )

    # 5. Determine real group composition.
    pairs_by_id = {pair.pair_id: pair for pair in pairs.pairs}

    def composition(group):
        labels = Counter(
            pairs_by_id[pair_id].label_class.value
            for pair_id in group.pair_ids
        )
        return (
            group.pair_count,
            labels["positive"],
            labels["negative_only"],
        )

    by_composition = {
        composition(group): group
        for group in groups.groups
    }

    expected = {
        (33, 8, 25),
        (13, 11, 2),
        (4, 0, 4),
    }

    if groups.group_count != 3 or set(by_composition) != expected:
        raise RuntimeError(
            "Real group composition differs from the approved "
            "Loop 1 baseline. Stop and review the inputs."
        )

    group_assignments = {
        by_composition[(33, 8, 25)].spatial_group_id:
            SpatialSplitName.TRAIN,
        by_composition[(4, 0, 4)].spatial_group_id:
            SpatialSplitName.VALIDATION,
        by_composition[(13, 11, 2)].spatial_group_id:
            SpatialSplitName.TEST,
    }

    # 6. Generate the official split catalog.
    catalog = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pairs,
        group_catalog=groups,
        policy=ASSIGNMENT_POLICY,
        output_name="komeh_spatial_split_v1",
        group_assignments=group_assignments,
    )

    errors = validate_spatial_split_catalog(
        catalog,
        pair_catalog=pairs,
    )
    if errors:
        raise RuntimeError("; ".join(errors))

    # 7. Verify the approved class distribution.
    distribution = {
        split.value: Counter(
            pairs_by_id[item.pair_id].label_class.value
            for item in catalog.assignments
            if item.split == split
        )
        for split in SpatialSplitName
    }

    expected_distribution = {
        "train": (33, 8, 25),
        "validation": (4, 0, 4),
        "test": (13, 11, 2),
    }

    for split, (total, positive, negative) in expected_distribution.items():
        observed = distribution[split]
        if (
            sum(observed.values()),
            observed["positive"],
            observed["negative_only"],
        ) != (total, positive, negative):
            raise RuntimeError(f"Unexpected distribution: {split}")

    # 8. Persist and verify a deterministic artifact.
    payload = asdict(catalog)
    payload["assignment_count"] = catalog.assignment_count
    payload["spatial_group_count"] = catalog.spatial_group_count

    catalog_id = "sha256:" + sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()
    payload["catalog_id"] = catalog_id

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    observed = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    normalized_payload = json.loads(canonical_json(payload))
    if observed != normalized_payload:
        raise RuntimeError("Persisted spatial split differs from memory.")

    for split, counts in distribution.items():
        print(
            f"{split}: total={sum(counts.values())}, "
            f"positive={counts['positive']}, "
            f"negative={counts['negative_only']}"
        )

    print(f"Spatial groups: {groups.group_count}")
    print(f"Assigned pairs: {catalog.assignment_count}")
    print(f"Catalog ID: {catalog_id}")
    print(f"Output: {OUTPUT_PATH}")
    print("PASS: Real spatial split catalog created and verified.")


if __name__ == "__main__":
    main()
