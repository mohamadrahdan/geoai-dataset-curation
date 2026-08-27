from pathlib import Path
from shutil import copyfile
import numpy as np
import pytest
import rasterio
from affine import Affine
from geoai_dataset_curation.image_construction.artifact_integration import (
    RasterArtifactGridMismatchError,
    retrieve_and_verify_raster_artifact,
)
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RasterArtifactRetrievalRequest,
    RemoteRasterArtifact,
    RetrievedRasterArtifact,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)


class FakeRasterArtifactRetriever:
    def __init__(
        self,
        source_path: Path,
    ) -> None:
        self._source_path = source_path

    def retrieve(
        self,
        request: RasterArtifactRetrievalRequest,
    ) -> RetrievedRasterArtifact:
        request.local_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        copyfile(
            self._source_path,
            request.local_path,
        )
        return RetrievedRasterArtifact(
            source=request.artifact,
            local_path=request.local_path,
        )


def _write_geotiff(
    path: Path,
    *,
    transform: Affine,
) -> None:
    data = np.zeros(
        (4, 8, 16),
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


def _approved_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=16,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        ),
    )


def test_retrieve_and_verify_raster_artifact_integrates_workflow(
    tmp_path: Path,
) -> None:
    source = tmp_path / "remote.tif"
    _write_geotiff(
        source,
        transform=Affine(
            10.0,
            0.0,
            500000.0,
            0.0,
            -10.0,
            3600000.0,
        ),
    )

    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri="drive://test/remote.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=(
            tmp_path
            / "retrieved"
            / "artifact.tif"
        ),
    )

    result = retrieve_and_verify_raster_artifact(
        retriever=FakeRasterArtifactRetriever(
            source
        ),
        request=request,
        approved_grid=_approved_grid(),
    )
    assert result.retrieval.exists is True
    assert result.retrieval.local_path.is_file()
    assert result.metadata.driver == "GTiff"
    assert result.metadata.crs == "EPSG:32639"
    assert result.metadata.width == 16
    assert result.metadata.height == 8
    assert result.metadata.band_count == 4
    assert result.grid_verification.matches is True


def test_retrieve_and_verify_raster_artifact_rejects_grid_mismatch(
    tmp_path: Path,
) -> None:
    source = tmp_path / "remote.tif"
    _write_geotiff(
        source,
        transform=Affine(
            10.0,
            0.0,
            500005.0,
            0.0,
            -10.0,
            3600000.0,
        ),
    )

    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri="drive://test/remote.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=(
            tmp_path
            / "retrieved"
            / "artifact.tif"
        ),
    )
    with pytest.raises(
        RasterArtifactGridMismatchError,
        match="does not match",
    ):
        retrieve_and_verify_raster_artifact(
            retriever=FakeRasterArtifactRetriever(
                source
            ),
            request=request,
            approved_grid=_approved_grid(),
        )