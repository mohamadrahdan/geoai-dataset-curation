"Cloud-masking contracts for Sentinel-2 image construction"
from dataclasses import dataclass


SENTINEL2_SCL_BAND = "SCL"
DEFAULT_SENTINEL2_EXCLUDED_SCL_CLASSES = (
    1,
    3,
    8,
    9,
    10,
    11,
)

@dataclass(frozen=True)
class Sentinel2CloudMaskSpec:
    "Explicit Sentinel-2 SCL cloud-masking policy"
    scl_band: str = SENTINEL2_SCL_BAND
    excluded_scl_classes: tuple[int, ...] = (
        DEFAULT_SENTINEL2_EXCLUDED_SCL_CLASSES
    )