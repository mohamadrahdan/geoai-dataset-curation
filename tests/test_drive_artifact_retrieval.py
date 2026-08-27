from pathlib import Path
from typing import Any
import pytest
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RasterArtifactRetrievalRequest,
    RemoteRasterArtifact,
)
from geoai_dataset_curation.image_construction.drive_artifact_retrieval import (
    GoogleDriveArtifactRetriever,
    parse_drive_artifact_uri,
)


def test_parse_drive_artifact_uri_returns_folder_and_file() -> None:
    folder, file_name = parse_drive_artifact_uri(
        "drive://exports/example.tif"
    )
    assert folder == "exports"
    assert file_name == "example.tif"


def test_parse_drive_artifact_uri_rejects_invalid_uri() -> None:
    with pytest.raises(
        ValueError,
        match="must start with drive://",
    ):
        parse_drive_artifact_uri(
            "https://example.com/example.tif"
        )


class FakeExecutableRequest:
    def __init__(
        self,
        result: Any,
    ) -> None:
        self._result = result
    def execute(self) -> Any:
        return self._result


class FakeDriveFilesResource:
    def __init__(self) -> None:
        self.list_calls: list[
            dict[str, object]
        ] = []
        self.get_media_calls: list[
            dict[str, object]
        ] = []

    def list(
        self,
        **kwargs: object,
    ) -> FakeExecutableRequest:
        self.list_calls.append(
            dict(kwargs)
        )
        query = str(
            kwargs["q"]
        )

        if (
            "application/vnd.google-apps.folder"
            in query
        ):
            return FakeExecutableRequest(
                {
                    "files": [
                        {
                            "id": "folder-123",
                            "name": "exports",
                        }
                    ]
                }
            )
        return FakeExecutableRequest(
            {
                "files": [
                    {
                        "id": "file-456",
                        "name": "example.tif",
                    }
                ]
            }
        )
    def get_media(
        self,
        **kwargs: object,
    ) -> FakeExecutableRequest:
        self.get_media_calls.append(
            dict(kwargs)
        )
        return FakeExecutableRequest(
            b"fake-geotiff-bytes"
        )


class FakeDriveService:
    def __init__(self) -> None:
        self.files_resource = (
            FakeDriveFilesResource()
        )
    def files(
        self,
    ) -> FakeDriveFilesResource:
        return self.files_resource
    

def test_drive_retriever_writes_remote_artifact_locally(
    tmp_path: Path,
) -> None:
    drive_service = FakeDriveService()

    retriever = GoogleDriveArtifactRetriever(
        drive_service
    )
    local_path = (
        tmp_path
        / "downloads"
        / "example.tif"
    )
    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri="drive://exports/example.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=local_path,
    )
    result = retriever.retrieve(
        request
    )
    assert result.source == request.artifact
    assert result.local_path == local_path
    assert result.exists is True
    assert local_path.read_bytes() == (
        b"fake-geotiff-bytes"
    )
    assert (
        drive_service
        .files_resource
        .get_media_calls
        == [
            {
                "fileId": "file-456",
            }
        ]
    )


class EmptyDriveFilesResource:
    def list(
        self,
        **kwargs: object,
    ) -> FakeExecutableRequest:
        return FakeExecutableRequest(
            {
                "files": [],
            }
        )


class EmptyDriveService:
    def files(
        self,
    ) -> EmptyDriveFilesResource:
        return EmptyDriveFilesResource()


def test_drive_retriever_rejects_missing_folder(
    tmp_path: Path,
) -> None:
    retriever = GoogleDriveArtifactRetriever(
        EmptyDriveService()
    )
    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri="drive://missing/example.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=tmp_path / "example.tif",
    )
    with pytest.raises(
        ValueError,
        match="Expected exactly one Google Drive folder",
    ):
        retriever.retrieve(
            request
        )