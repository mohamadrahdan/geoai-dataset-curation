from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)


def test_inspect_raster_artifact_reads_basic_metadata(
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.tif"
    transform = from_origin(
        500000.0,
        3600000.0,
        10.0,
        10.0,
    )
    data = np.zeros(
        (
            4,
            8,
            16,
        ),
        dtype="uint16",
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=16,
        height=8,
        count=4,
        dtype="uint16",
        crs="EPSG:32639",
        transform=transform,
    ) as dataset:
        dataset.write(data)

    metadata = inspect_raster_artifact(
        path
    )
    assert metadata.path == path
    assert metadata.driver == "GTiff"
    assert metadata.crs == "EPSG:32639"
    assert metadata.width == 16
    assert metadata.height == 8
    assert metadata.band_count == 4
    assert metadata.dtypes == (
        "uint16",
        "uint16",
        "uint16",
        "uint16",
    )
    assert metadata.transform == transform


def test_inspect_raster_artifact_rejects_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.tif"
    try:
        inspect_raster_artifact(
            path
        )
    except FileNotFoundError as exc:
        assert "Raster artifact does not exist" in str(exc)
    else:
        raise AssertionError(
            "Expected FileNotFoundError."
        )