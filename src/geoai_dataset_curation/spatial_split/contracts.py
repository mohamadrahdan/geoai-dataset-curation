"Contracts for leakage-aware spatial dataset splits"
from dataclasses import dataclass
from enum import StrEnum


class SpatialSplitName(StrEnum):
    "Allowed dataset split names"
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION = (
    "spatial-split-catalog-v1"
)


@dataclass(frozen=True)
class SpatialSplitAssignment:
    "One pair assigned through one indivisible spatial group"
    pair_id: str
    tile_id: str
    spatial_group_id: str
    split: SpatialSplitName


@dataclass(frozen=True)
class SpatialSplitCatalog:
    "Version-linked assignments for one spatial dataset split"
    schema_version: str
    output_name: str
    pair_catalog_id: str
    pair_qc_report_id: str
    visual_review_catalog_id: str
    grouping_policy_id: str
    assignment_policy_id: str
    assignments: tuple[SpatialSplitAssignment, ...]

    @property
    def assignment_count(self) -> int:
        "Return the number of assigned pairs"
        return len(self.assignments)

    @property
    def spatial_group_count(self) -> int:
        "Return the number of distinct spatial groups"
        return len(
            {
                assignment.spatial_group_id
                for assignment in self.assignments
            }
        )

    @property
    def train_count(self) -> int:
        "Return the number of training assignments"
        return sum(
            assignment.split == SpatialSplitName.TRAIN
            for assignment in self.assignments
        )

    @property
    def validation_count(self) -> int:
        "Return the number of validation assignments"
        return sum(
            assignment.split
            == SpatialSplitName.VALIDATION
            for assignment in self.assignments
        )

    @property
    def test_count(self) -> int:
        "Return the number of test assignments"
        return sum(
            assignment.split == SpatialSplitName.TEST
            for assignment in self.assignments
        )


@dataclass(frozen=True)
class SpatialSplitInputAcceptance:
    "Accepted pair population and its exact QC evidence"
    pair_catalog_id: str
    pair_qc_report_id: str
    visual_review_catalog_id: str
    pair_ids: tuple[str, ...]
    tile_ids: tuple[str, ...]

    @property
    def pair_count(self) -> int:
        "Return the number of accepted pairs"
        return len(self.pair_ids)