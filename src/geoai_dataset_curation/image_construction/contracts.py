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


@dataclass(frozen=True)
class ImageConstructionResult:
    "Summary of one image-construction run"

    source_id: str
    output_name: str
    scene_count: int
    band_count: int
    grid: RasterGridSpec
    artifact_uri: str

    @property
    def has_artifact(self) -> bool:
        "Return whether a constructed raster artifact is available"
        
        return bool(self.artifact_uri.strip())