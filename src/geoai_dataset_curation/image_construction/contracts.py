"Contracts for raster image construction"

from dataclasses import dataclass


@dataclass(frozen=True)
class RasterGridSpec:
    "Target raster-grid definition for image construction"

    crs: str
    width: int
    height: int
    pixel_size_x: float
    pixel_size_y: float


@dataclass(frozen=True)
class ImageConstructionRequest:
    "Input contract for constructing one raster image"

    source_id: str
    scene_ids: tuple[str, ...]
    bands: tuple[str, ...]
    grid: RasterGridSpec
    output_name: str