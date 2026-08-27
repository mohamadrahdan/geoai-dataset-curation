from pathlib import Path
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RasterArtifactRetrievalRequest,
    RemoteRasterArtifact,
    RetrievedRasterArtifact,
)


def test_remote_raster_artifact_preserves_uri_and_format() -> None:
    artifact = RemoteRasterArtifact(
        uri="drive://geoai-dataset-curation-smoke/tiny_live_export_smoke.tif",
        format=RasterArtifactFormat.GEOTIFF,
    )
    assert (
        artifact.uri
        == "drive://geoai-dataset-curation-smoke/tiny_live_export_smoke.tif"
    )
    assert artifact.format is RasterArtifactFormat.GEOTIFF


def test_retrieval_request_preserves_remote_artifact_and_local_path(
    tmp_path: Path,
) -> None:
    artifact = RemoteRasterArtifact(
        uri="drive://exports/example.tif",
        format=RasterArtifactFormat.GEOTIFF,
    )
    local_path = tmp_path / "example.tif"
    request = RasterArtifactRetrievalRequest(
        artifact=artifact,
        local_path=local_path,
    )
    assert request.artifact == artifact
    assert request.local_path == local_path


def test_retrieved_raster_artifact_reports_existing_local_file(
    tmp_path: Path,
) -> None:
    local_path = tmp_path / "example.tif"
    local_path.write_bytes(b"test")
    artifact = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri="drive://exports/example.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=local_path,
    )
    assert artifact.exists is True


def test_retrieved_raster_artifact_reports_missing_local_file(
    tmp_path: Path,
) -> None:
    artifact = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri="drive://exports/missing.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=tmp_path / "missing.tif",
    )
    assert artifact.exists is False