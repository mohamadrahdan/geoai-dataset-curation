"Contracts for deterministic candidate-tile sampling"
from dataclasses import dataclass
from enum import StrEnum
from geoai_dataset_curation.tiling.catalog import TileLabelClass


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