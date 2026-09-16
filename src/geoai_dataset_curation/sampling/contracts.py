"Contracts for deterministic candidate-tile sampling"
from dataclasses import dataclass
from enum import StrEnum
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileLabelClass,
)


class SamplingEligibilityStatus(StrEnum):
    "Whether one candidate may enter supervised sampling"
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class SamplingEligibilityReason(StrEnum):
    "Reason for one candidate's sampling eligibility status"
    SUPERVISED_PIXELS_PRESENT = "supervised_pixels_present"
    ALL_PIXELS_IGNORED = "all_pixels_ignored"


class SamplingOrder(StrEnum):
    "Deterministic ordering used by one sampling selection"
    CATALOG_ORDER = "catalog_order"


class HardNegativeHandling(StrEnum):
    "Required treatment of hard-negative source evidence"
    REQUIRE_SOURCE_PROVENANCE = "require_source_provenance"


class NegativeProvenanceKind(StrEnum):
    "Source-derived negative evidence present in one tile"
    NONE = "none"
    ORDINARY_NEGATIVE = "ordinary_negative"
    HARD_NEGATIVE = "hard_negative"
    MIXED_NEGATIVE = "mixed_negative"


@dataclass(frozen=True)
class SamplingPolicy:
    "Policy governing supervised candidate-tile selection"
    select_all_eligible: bool
    exclude_all_ignore: bool
    order: SamplingOrder
    hard_negative_handling: HardNegativeHandling


@dataclass(frozen=True)
class TileSamplingEligibility:
    "Eligibility assessment for one candidate tile"
    tile_id: str
    label_class: TileLabelClass
    status: SamplingEligibilityStatus
    reason: SamplingEligibilityReason

    @property
    def is_eligible(self) -> bool:
        "Return whether the candidate may enter supervised sampling"
        return self.status == SamplingEligibilityStatus.ELIGIBLE


@dataclass(frozen=True)
class TileSamplingSelection:
    "Auditable result of selecting supervised candidate tiles"
    catalog_id: str
    selected_candidates: tuple[TileCandidateRecord, ...]
    excluded_tile_ids: tuple[str, ...]

    @property
    def selected_tile_count(self) -> int:
        "Return the number of selected supervised candidates"
        return len(self.selected_candidates)

    @property
    def selected_positive_tile_count(self) -> int:
        "Return the number of selected positive candidates"
        return sum(
            candidate.label_class == TileLabelClass.POSITIVE
            for candidate in self.selected_candidates
        )

    @property
    def selected_negative_only_tile_count(self) -> int:
        "Return the number of selected negative-only candidates"
        return sum(
            candidate.label_class
            == TileLabelClass.NEGATIVE_ONLY
            for candidate in self.selected_candidates
        )

    @property
    def excluded_tile_count(self) -> int:
        "Return the number of candidates excluded from sampling"
        return len(self.excluded_tile_ids)


TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION = ("tile-negative-provenance-v1")
TILE_SAMPLING_SELECTION_SCHEMA_VERSION = "tile-sampling-selection-v1"
@dataclass(frozen=True)
class TileNegativeProvenance:
    "Source-specific negative evidence measured for one tile"
    tile_id: str
    ordinary_negative_pixel_count: int
    hard_negative_pixel_count: int
    shared_negative_pixel_count: int

    @property
    def union_negative_pixel_count(self) -> int:
        "Return unique pixels covered by either negative source"
        return (
            self.ordinary_negative_pixel_count
            + self.hard_negative_pixel_count
            - self.shared_negative_pixel_count
        )

    @property
    def kind(self) -> NegativeProvenanceKind:
        "Return the source-derived negative-evidence class"
        has_ordinary = (self.ordinary_negative_pixel_count > 0)
        has_hard = (self.hard_negative_pixel_count > 0)
        if has_ordinary and has_hard:
            return NegativeProvenanceKind.MIXED_NEGATIVE
        if has_hard:
            return NegativeProvenanceKind.HARD_NEGATIVE
        if has_ordinary:
            return NegativeProvenanceKind.ORDINARY_NEGATIVE
        return NegativeProvenanceKind.NONE


@dataclass(frozen=True)
class TileNegativeProvenanceCatalog:
    "Source-linked negative provenance for one tile catalog"
    schema_version: str
    tile_catalog_id: str
    ordinary_negative_source_id: str
    hard_negative_source_id: str
    records: tuple[TileNegativeProvenance, ...]

    @property
    def record_count(self) -> int:
        "Return the number of tile-level provenance records"
        return len(self.records)

    @property
    def hard_negative_tile_count(self) -> int:
        "Return tiles containing any hard-negative evidence"
        return sum(
            record.kind in {
                NegativeProvenanceKind.HARD_NEGATIVE,
                NegativeProvenanceKind.MIXED_NEGATIVE,
            }
            for record in self.records
        )