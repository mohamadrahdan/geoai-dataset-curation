"Expected artifact contracts for Loop 1 label rasters"
from dataclasses import dataclass
from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.image_construction.contracts import RasterGridSpec
from geoai_dataset_curation.label_rasterization.contracts import (
    LabelRasterizationRequest,
)


LOOP1_LABEL_ALLOWED_VALUES = tuple(
    int(value)
    for value in LabelValue
)


@dataclass(frozen=True)
class LabelRasterArtifactSpec:
    "Expected structure of one Loop 1 label-raster artifact"
    output_name: str
    grid: RasterGridSpec
    band_count: int = 1
    dtype: str = "uint8"
    allowed_values: tuple[int, ...] = LOOP1_LABEL_ALLOWED_VALUES


def create_label_raster_artifact_spec(
    request: LabelRasterizationRequest,
) -> LabelRasterArtifactSpec:
    "Create the expected label-artifact contract from a rasterization request"
    return LabelRasterArtifactSpec(
        output_name=request.output_name,
        grid=request.grid,
    )