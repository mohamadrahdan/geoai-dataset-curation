"Deterministic assignment of spatial groups."
from dataclasses import dataclass
import hashlib
from math import isclose, isfinite
from numbers import Real
from typing import Any
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split.contracts import (
    SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION,
    SpatialSplitAssignment,
    SpatialSplitCatalog,
    SpatialSplitInputAcceptance,
    SpatialSplitName,
)
from geoai_dataset_curation.spatial_split.relationship_contracts import (
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
)
from geoai_dataset_curation.spatial_split.relationship_identity import (
    build_spatial_leakage_group_id,
)
from geoai_dataset_curation.spatial_split.validation import (
    validate_spatial_split_catalog,
)
from geoai_dataset_curation.tiling import TileLabelClass
from geoai_dataset_curation.tiling.identity import _build_sha256_id
from collections.abc import Mapping


SPATIAL_ASSIGNMENT_POLICY_SCHEMA_VERSION = "spatial-assignment-policy-v1"

_SPLITS = (
    SpatialSplitName.TRAIN,
    SpatialSplitName.VALIDATION,
    SpatialSplitName.TEST,
)


@dataclass(frozen=True)
class SpatialAssignmentPolicy:
    train_fraction: float
    validation_fraction: float
    test_fraction: float
    seed: int

    def fraction_for(self, split: SpatialSplitName) -> float:
        return {
            SpatialSplitName.TRAIN: self.train_fraction,
            SpatialSplitName.VALIDATION: self.validation_fraction,
            SpatialSplitName.TEST: self.test_fraction,
        }[split]


def _is_fraction(value: object) -> bool:
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and isfinite(float(value))
        and 0 < float(value) < 1
    )


def validate_spatial_assignment_policy(
    policy: SpatialAssignmentPolicy,
) -> tuple[str, ...]:
    errors: list[str] = []
    fractions = (
        policy.train_fraction,
        policy.validation_fraction,
        policy.test_fraction,
    )

    for field_name, value in (
        ("train_fraction", policy.train_fraction),
        ("validation_fraction", policy.validation_fraction),
        ("test_fraction", policy.test_fraction),
    ):
        if not _is_fraction(value):
            errors.append(f"{field_name} must be between zero and one.")

    if all(_is_fraction(value) for value in fractions):
        if not isclose(sum(fractions), 1.0, rel_tol=0.0, abs_tol=1e-9):
            errors.append("split fractions must sum to one.")

    if (
        not isinstance(policy.seed, int)
        or isinstance(policy.seed, bool)
        or policy.seed < 0
    ):
        errors.append("seed must be a non-negative integer.")

    return tuple(errors)


def spatial_assignment_policy_identity_payload(
    policy: SpatialAssignmentPolicy,
) -> dict[str, Any]:
    errors = validate_spatial_assignment_policy(policy)
    if errors:
        raise ValueError("Cannot identify invalid assignment policy: " + "; ".join(errors))

    return {
        "schema_version": SPATIAL_ASSIGNMENT_POLICY_SCHEMA_VERSION,
        "train_fraction": policy.train_fraction,
        "validation_fraction": policy.validation_fraction,
        "test_fraction": policy.test_fraction,
        "seed": policy.seed,
        "algorithm": "seeded_greedy_pair_and_label_balance",
    }


def build_spatial_assignment_policy_id(
    policy: SpatialAssignmentPolicy,
) -> str:
    return _build_sha256_id(spatial_assignment_policy_identity_payload(policy))


def _validate_assignment_inputs(
    acceptance: SpatialSplitInputAcceptance,
    *,
    pair_catalog: ImageMaskPairCatalog,
    group_catalog: SpatialLeakageGroupCatalog,
    policy: SpatialAssignmentPolicy,
    output_name: str,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(output_name, str) or not output_name.strip():
        errors.append("output_name must not be empty.")

    policy_errors = validate_spatial_assignment_policy(policy)
    errors.extend(f"policy.{error}" for error in policy_errors)

    pair_catalog_id = build_image_mask_pair_catalog_id(pair_catalog)
    if acceptance.pair_catalog_id != pair_catalog_id:
        errors.append("acceptance pair_catalog_id must match the pair catalog.")

    if group_catalog.pair_catalog_id != pair_catalog_id:
        errors.append("group catalog pair_catalog_id must match the pair catalog.")

    pair_ids = tuple(pair.pair_id for pair in pair_catalog.pairs)
    tile_ids = tuple(pair.tile_id for pair in pair_catalog.pairs)

    if acceptance.pair_ids != pair_ids:
        errors.append("acceptance pair_ids must match the pair catalog order.")

    if acceptance.tile_ids != tile_ids:
        errors.append("acceptance tile_ids must match the pair catalog order.")

    if len(group_catalog.groups) < 3:
        errors.append("at least three spatial groups are required.")

    grouped_pair_ids = tuple(
        pair_id
        for group in group_catalog.groups
        for pair_id in group.pair_ids
    )
    grouped_tile_ids = tuple(
        tile_id
        for group in group_catalog.groups
        for tile_id in group.tile_ids
    )

    if len(set(grouped_pair_ids)) != len(grouped_pair_ids):
        errors.append("pair_id values must not appear in multiple groups.")

    if len(set(grouped_tile_ids)) != len(grouped_tile_ids):
        errors.append("tile_id values must not appear in multiple groups.")

    if set(grouped_pair_ids) != set(pair_ids):
        errors.append("groups must cover every pair exactly once.")

    pairs_by_id = {
        pair.pair_id: pair
        for pair in pair_catalog.pairs
    }
    for group_index, group in enumerate(group_catalog.groups):
        expected_group_id = build_spatial_leakage_group_id(
            pair_ids=group.pair_ids,
            tile_ids=group.tile_ids,
        )
        if group.spatial_group_id != expected_group_id:
            errors.append(
                f"groups[{group_index}].spatial_group_id must match membership."
            )

        expected_tile_ids = tuple(
            pairs_by_id[pair_id].tile_id
            for pair_id in group.pair_ids
            if pair_id in pairs_by_id
        )
        if group.tile_ids != expected_tile_ids:
            errors.append(f"groups[{group_index}].tile_ids must match its pair_ids.")

    unsupported_pair_ids = tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
        if pair.label_class not in {
            TileLabelClass.POSITIVE,
            TileLabelClass.NEGATIVE_ONLY,
        }
    )
    if unsupported_pair_ids:
        errors.append("every pair must be positive or negative-only.")

    return tuple(errors)


def _seeded_group_key(
    group: SpatialLeakageGroup,
    seed: int,
) -> tuple[int, str]:
    payload = f"{seed}:{group.spatial_group_id}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return -group.pair_count, digest


def _group_label_counts(
    group: SpatialLeakageGroup,
    pairs_by_id: dict[str, Any],
) -> tuple[int, int]:
    positive_count = sum(
        pairs_by_id[pair_id].label_class == TileLabelClass.POSITIVE
        for pair_id in group.pair_ids
    )
    negative_count = group.pair_count - positive_count
    return positive_count, negative_count


def _assignment_score(
    *,
    candidate_split: SpatialSplitName,
    group_counts: tuple[int, int, int],
    current_counts: dict[SpatialSplitName, list[int]],
    targets: dict[SpatialSplitName, tuple[float, float, float]],
) -> float:
    score = 0.0

    for split in _SPLITS:
        actual = current_counts[split].copy()
        if split == candidate_split:
            actual = [
                actual[index] + group_counts[index]
                for index in range(3)
            ]

        for observed, target in zip(actual, targets[split], strict=True):
            if target > 0:
                score += ((observed - target) / target) ** 2

    return score


def _assign_groups(
    groups: tuple[SpatialLeakageGroup, ...],
    *,
    pair_catalog: ImageMaskPairCatalog,
    policy: SpatialAssignmentPolicy,
) -> dict[str, SpatialSplitName]:
    pairs_by_id = {
        pair.pair_id: pair
        for pair in pair_catalog.pairs
    }
    total_positive = sum(
        pair.label_class == TileLabelClass.POSITIVE
        for pair in pair_catalog.pairs
    )
    total_negative = pair_catalog.pair_count - total_positive

    targets = {
        split: (
            pair_catalog.pair_count * policy.fraction_for(split),
            total_positive * policy.fraction_for(split),
            total_negative * policy.fraction_for(split),
        )
        for split in _SPLITS
    }
    current_counts = {
        split: [0, 0, 0]
        for split in _SPLITS
    }
    split_by_group_id: dict[str, SpatialSplitName] = {}
    ordered_groups = tuple(
        sorted(
            groups,
            key=lambda group: _seeded_group_key(group, policy.seed),
        )
    )

    for index, group in enumerate(ordered_groups):
        positive_count, negative_count = _group_label_counts(
            group,
            pairs_by_id,
        )
        group_counts = (
            group.pair_count,
            positive_count,
            negative_count,
        )
        empty_splits = tuple(
            split
            for split in _SPLITS
            if current_counts[split][0] == 0
        )
        remaining_group_count = len(ordered_groups) - index

        candidate_splits = _SPLITS
        if remaining_group_count == len(empty_splits):
            candidate_splits = empty_splits

        selected_split = min(
            candidate_splits,
            key=lambda split: (
                _assignment_score(
                    candidate_split=split,
                    group_counts=group_counts,
                    current_counts=current_counts,
                    targets=targets,
                ),
                _SPLITS.index(split),
            ),
        )
        split_by_group_id[group.spatial_group_id] = selected_split
        current_counts[selected_split] = [
            current_counts[selected_split][count_index]
            + group_counts[count_index]
            for count_index in range(3)
        ]

    return split_by_group_id


def _validate_explicit_group_assignments(
    group_catalog: SpatialLeakageGroupCatalog,
    group_assignments: Mapping[str, SpatialSplitName],
) -> dict[str, SpatialSplitName]:
    expected_ids = {
        group.spatial_group_id
        for group in group_catalog.groups
    }

    if set(group_assignments) != expected_ids:
        raise ValueError("Explicit assignments must cover every spatial group exactly once.")

    valid_splits = set(_SPLITS)
    if any(
        not isinstance(split, SpatialSplitName)
        or split not in valid_splits
        for split in group_assignments.values()
    ):
        raise ValueError("Invalid spatial split name.")

    if set(group_assignments.values()) != valid_splits:
        raise ValueError("Train, validation, and test must all receive a group.")

    return dict(group_assignments)


def build_spatial_split_catalog(
    acceptance: SpatialSplitInputAcceptance,
    *,
    pair_catalog: ImageMaskPairCatalog,
    group_catalog: SpatialLeakageGroupCatalog,
    policy: SpatialAssignmentPolicy,
    output_name: str,
    group_assignments: Mapping[str, SpatialSplitName] | None = None,
) -> SpatialSplitCatalog:
    errors = _validate_assignment_inputs(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=policy,
        output_name=output_name,
    )
    if errors:
        raise ValueError("Cannot assign spatial groups: " + "; ".join(errors))

    if group_assignments is None:
        split_by_group_id = _assign_groups(
            group_catalog.groups,
            pair_catalog=pair_catalog,
            policy=policy,
        )
        assignment_policy_id = build_spatial_assignment_policy_id(
            policy
        )
    else:
        split_by_group_id = _validate_explicit_group_assignments(
            group_catalog,
            group_assignments,
        )

        assignment_policy_id = _build_sha256_id({
            "schema_version": SPATIAL_ASSIGNMENT_POLICY_SCHEMA_VERSION,
            "mode": "explicit_group_assignment",
            "base_policy_id": build_spatial_assignment_policy_id(
                policy
            ),
            "assignments": [
                {
                    "spatial_group_id": group_id,
                    "split": split.value,
                }
                for group_id, split in sorted(
                    split_by_group_id.items()
                )
            ],
        })
    group_by_pair_id = {
        pair_id: group
        for group in group_catalog.groups
        for pair_id in group.pair_ids
    }
    assignments = tuple(
        SpatialSplitAssignment(
            pair_id=pair.pair_id,
            tile_id=pair.tile_id,
            spatial_group_id=group_by_pair_id[pair.pair_id].spatial_group_id,
            split=split_by_group_id[
                group_by_pair_id[pair.pair_id].spatial_group_id
            ],
        )
        for pair in pair_catalog.pairs
    )
    catalog = SpatialSplitCatalog(
        schema_version=SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION,
        output_name=output_name.strip(),
        pair_catalog_id=acceptance.pair_catalog_id,
        pair_qc_report_id=acceptance.pair_qc_report_id,
        visual_review_catalog_id=acceptance.visual_review_catalog_id,
        grouping_policy_id=group_catalog.grouping_policy_id,
        assignment_policy_id=assignment_policy_id,
        assignments=assignments,
    )

    catalog_errors = validate_spatial_split_catalog(
        catalog,
        pair_catalog=pair_catalog,
    )
    if catalog_errors:
        raise ValueError(
            "Cannot build invalid spatial split catalog: "
            + "; ".join(catalog_errors)
        )

    return catalog