from pathlib import Path
import numpy as np
import rasterio
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterArtifactSpec,
    write_label_raster_artifact,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=4,
        height=3,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3500000.0,
        ),
    )


def test_label_raster_is_written_as_uint8_geotiff(
    tmp_path: Path,
) -> None:
    data = np.array(
        [
            [255, 255, 255, 255],
            [255, 1, 0, 255],
            [255, 255, 255, 255],
        ],
        dtype=np.uint8,
    )
    spec = LabelRasterArtifactSpec(
        output_name="labels",
        grid=make_grid(),
    )
    output_path = (
        tmp_path / "labels.tif"
    )
    result_path = write_label_raster_artifact(
        data=data,
        spec=spec,
        output_path=output_path,
    )
    assert result_path == output_path
    with rasterio.open(result_path) as dataset:
        assert dataset.count == 1
        assert dataset.dtypes == ("uint8",)
        assert dataset.crs.to_string() == "EPSG:32639"
        assert dataset.width == 4
        assert dataset.height == 3
        assert dataset.read(1).dtype == np.uint8