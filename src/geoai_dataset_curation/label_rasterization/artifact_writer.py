"Writing physical Loop 1 label-raster artifacts"
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
from geoai_dataset_curation.label_rasterization.artifact_contract import (
    LabelRasterArtifactSpec,
)


def write_label_raster_artifact(
    *,
    data: np.ndarray,
    spec: LabelRasterArtifactSpec,
    output_path: Path,
) -> Path:
    "Write one verified-structure label array as a GeoTIFF"
    if data.shape != (
        spec.grid.height,
        spec.grid.width,
    ):
        raise ValueError(
            "Label array shape does not match "
            "the artifact grid."
        )
    if data.dtype != np.uint8:
        raise ValueError("Label array dtype must be uint8.")

    transform = spec.grid.transform
    if transform is None:
        raise ValueError("Label artifact requires an affine transform.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        width=spec.grid.width,
        height=spec.grid.height,
        count=spec.band_count,
        dtype=spec.dtype,
        crs=spec.grid.crs,
        transform=Affine(*transform.as_tuple),
        compress="deflate",
    ) as dataset:
        dataset.write(
            data,
            1,
        )

    return output_path