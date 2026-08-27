from __future__ import annotations
import sys
from pathlib import Path
import google.auth
from googleapiclient.discovery import build
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RasterArtifactRetrievalRequest,
    RemoteRasterArtifact,
)
from geoai_dataset_curation.image_construction.drive_artifact_retrieval import (
    GoogleDriveArtifactRetriever,
)


DRIVE_SCOPE = (
    "https://www.googleapis.com/auth/drive.readonly"
)

REMOTE_URI = (
    "drive://geoai-dataset-curation-smoke/"
    "tiny_live_export_smoke.tif"
)

LOCAL_PATH = Path(
    "artifacts/live/tiny_live_export_smoke.tif"
)


def main() -> int:
    try:
        credentials, _ = (
            google.auth.default(
                scopes=[
                    DRIVE_SCOPE,
                ]
            )
        )
    except Exception as exc:
        print(
            "FAIL: Google credentials could not be loaded."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 2

    try:
        drive_service = build(
            "drive",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
    except Exception as exc:
        print(
            "FAIL: Google Drive service could not be created."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 3

    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri=REMOTE_URI,
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=LOCAL_PATH,
    )

    retriever = GoogleDriveArtifactRetriever(
        drive_service
    )

    try:
        result = retriever.retrieve(
            request
        )
    except Exception as exc:
        print(
            "FAIL: Drive artifact retrieval failed."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 4

    if not result.exists:
        print(
            "FAIL: Retrieved artifact does not exist locally."
        )
        return 5

    file_size = (
        result.local_path.stat().st_size
    )
    if file_size <= 0:
        print(
            "FAIL: Retrieved artifact is empty."
        )
        return 6
    print(
        "PASS: Drive artifact retrieval succeeded."
    )
    print(
        f"Remote URI: {result.source.uri}"
    )
    print(
        f"Local path: {result.local_path}"
    )
    print(
        f"File size: {file_size} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )