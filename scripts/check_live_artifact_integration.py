from __future__ import annotations
from pathlib import Path
import google.auth
from googleapiclient.discovery import build
from geoai_dataset_curation.image_construction.artifact_integration import (
    retrieve_and_verify_raster_artifact,
)
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RasterArtifactRetrievalRequest,
    RemoteRasterArtifact,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.drive_artifact_retrieval import (
    GoogleDriveArtifactRetriever,
)

DRIVE_SCOPE = ("https://www.googleapis.com/auth/drive.readonly")

REMOTE_URI = (
    "drive://geoai-dataset-curation-smoke/"
    "tiny_live_export_smoke.tif"
)

LOCAL_PATH = Path(
    "artifacts/live/integration/"
    "tiny_live_export_smoke.tif"
)

APPROVED_GRID = RasterGridSpec(
    crs="EPSG:32639",
    width=97,
    height=112,
    pixel_size_x=10.0,
    pixel_size_y=10.0,
    transform=AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=547020.0,
        d=0.0,
        e=-10.0,
        f=3374300.0,
    ),
)


def main() -> int:
    credentials, _ = google.auth.default(
        scopes=[
            DRIVE_SCOPE,
        ]
    )
    drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    retriever = GoogleDriveArtifactRetriever(
        drive_service
    )

    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri=REMOTE_URI,
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=LOCAL_PATH,
    )

    result = retrieve_and_verify_raster_artifact(
        retriever=retriever,
        request=request,
        approved_grid=APPROVED_GRID,
    )

    print("PASS: Live artifact integration succeeded.")
    print(f"Remote URI: {result.retrieval.source.uri}")
    print(f"Local path: {result.retrieval.local_path}")
    print(f"CRS: {result.metadata.crs}")
    print(
        f"Dimensions: "
        f"{result.metadata.width} x "
        f"{result.metadata.height}"
    )
    print(f"Bands: {result.metadata.band_count}")
    print(f"Transform: {result.metadata.transform}")
    print(
        "Approved grid match: "
        f"{result.grid_verification.matches}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )