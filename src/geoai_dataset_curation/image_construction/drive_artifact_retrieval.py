"Google Drive retrieval for exported raster artifacts"
from __future__ import annotations
from pathlib import Path
from typing import Any
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactRetrievalRequest,
    RetrievedRasterArtifact,
)


DRIVE_URI_PREFIX = "drive://"


def parse_drive_artifact_uri(
    uri: str,
) -> tuple[str, str]:
    "Return Drive folder and file name from one artifact URI"
    if not uri.startswith(DRIVE_URI_PREFIX):
        raise ValueError(
            "Drive artifact URI must start with "
            f"{DRIVE_URI_PREFIX}"
        )
    relative_path = uri[
        len(DRIVE_URI_PREFIX):
    ]
    parts = relative_path.split(
        "/",
        maxsplit=1,
    )
    if (
        len(parts) != 2
        or not parts[0].strip()
        or not parts[1].strip()
    ):
        raise ValueError(
            "Drive artifact URI must contain "
            "a folder and file name."
        )
    return (
        parts[0],
        parts[1],
    )


class GoogleDriveArtifactRetriever:
    "Retrieve exported raster artifacts from Google Drive"
    def __init__(
        self,
        drive_service: Any,
    ) -> None:
        self._drive_service = drive_service

    def retrieve(
        self,
        request: RasterArtifactRetrievalRequest,
    ) -> RetrievedRasterArtifact:
        "Retrieve one Drive artifact to local storage"
        folder_name, file_name = (
            parse_drive_artifact_uri(
                request.artifact.uri
            )
        )
        folder_id = self._find_folder_id(
            folder_name
        )
        file_id = self._find_file_id(
            folder_id=folder_id,
            file_name=file_name,
        )
        content = (
            self._drive_service
            .files()
            .get_media(
                fileId=file_id
            )
            .execute()
        )
        request.local_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        request.local_path.write_bytes(
            content
        )
        return RetrievedRasterArtifact(
            source=request.artifact,
            local_path=request.local_path,
        )

    def _find_folder_id(
        self,
        folder_name: str,
    ) -> str:
        query = (
            "mimeType = "
            "'application/vnd.google-apps.folder' "
            f"and name = '{folder_name}' "
            "and trashed = false"
        )
        result = (
            self._drive_service
            .files()
            .list(
                q=query,
                fields="files(id,name)",
            )
            .execute()
        )

        files = result.get(
            "files",
            []
        )

        if len(files) != 1:
            raise ValueError(
                "Expected exactly one Google Drive folder "
                f"named {folder_name!r}; "
                f"found {len(files)}."
            )

        return str(
            files[0]["id"]
        )

    def _find_file_id(
        self,
        *,
        folder_id: str,
        file_name: str,
    ) -> str:
        query = (
            f"'{folder_id}' in parents "
            f"and name = '{file_name}' "
            "and trashed = false"
        )
        result = (
            self._drive_service
            .files()
            .list(
                q=query,
                fields="files(id,name)",
            )
            .execute()
        )

        files = result.get(
            "files",
            []
        )
        if len(files) != 1:
            raise ValueError(
                "Expected exactly one Google Drive file "
                f"named {file_name!r}; "
                f"found {len(files)}."
            )
        return str(
            files[0]["id"]
        )