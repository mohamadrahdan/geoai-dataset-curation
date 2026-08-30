"Rasterization-policy contracts for label construction"
from dataclasses import dataclass
from enum import StrEnum
from geoai_dataset_curation.contracts import LabelValue


class PixelInclusionRule(StrEnum):
    "Rule used to decide whether a polygon labels a raster pixel"
    PIXEL_CENTER = "pixel_center"


class OverlapRule(StrEnum):
    "Rule used when supervision sources overlap"
    ERROR_ON_CONFLICT = "error_on_conflict"


class OutOfGridRule(StrEnum):
    "Rule used when supervision geometries cross the raster-grid boundary"
    CLIP_PARTIAL_REJECT_DISJOINT = "clip_partial_reject_disjoint"


@dataclass(frozen=True)
class LabelRasterizationPolicy:
    "Deterministic rasterization policy for Loop 1 labels"
    pixel_inclusion: PixelInclusionRule = PixelInclusionRule.PIXEL_CENTER
    overlap: OverlapRule = OverlapRule.ERROR_ON_CONFLICT
    out_of_grid: OutOfGridRule = OutOfGridRule.CLIP_PARTIAL_REJECT_DISJOINT
    fill_value: LabelValue = LabelValue.IGNORE


LOOP1_RASTERIZATION_POLICY = LabelRasterizationPolicy()