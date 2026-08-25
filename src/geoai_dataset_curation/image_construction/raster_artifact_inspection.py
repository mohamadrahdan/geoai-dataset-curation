"Inspection helpers for retrieved raster artifacts"
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import rasterio
from affine import Affine


@dataclass(frozen=True)
class RasterArtifactMetadata:
    "Basic metadata read from one local raster artifact"
    path: Path
    driver: str
    crs: str | None
    width: int
    height: int
    band_count: int
    dtypes: tuple[str, ...]
    transform: Affine


def inspect_raster_artifact(
    path: Path,
) -> RasterArtifactMetadata:
    "Open one raster artifact and return its basic metadata"
    if not path.is_file():
        raise FileNotFoundError(
            f"Raster artifact does not exist: {path}"
        )

    with rasterio.open(path) as dataset:
        crs = (
            dataset.crs.to_string()
            if dataset.crs is not None
            else None
        )

        return RasterArtifactMetadata(
            path=path,
            driver=dataset.driver,
            crs=crs,
            width=dataset.width,
            height=dataset.height,
            band_count=dataset.count,
            dtypes=tuple(dataset.dtypes),
            transform=dataset.transform,
        )