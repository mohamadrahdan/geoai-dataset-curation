"Contracts for vector-to-label-raster conversion"
from dataclasses import dataclass
from shapely.geometry.base import BaseGeometry
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import RasterGridSpec
from geoai_dataset_curation.label_rasterization.policy import (
    LOOP1_RASTERIZATION_POLICY,
    LabelRasterizationPolicy,
)


@dataclass(frozen=True)
class LabelVectorSource:
    "One vector source carrying explicit supervision evidence"
    source_id: str
    supervision: SupervisionKind
    geometries: tuple[BaseGeometry, ...]


@dataclass(frozen=True)
class LabelRasterizationRequest:
    "Input contract for constructing one label raster"
    sources: tuple[LabelVectorSource, ...]
    grid: RasterGridSpec
    output_name: str
    policy: LabelRasterizationPolicy = LOOP1_RASTERIZATION_POLICY