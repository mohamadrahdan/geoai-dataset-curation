"Retrieve and verify the real production-style raster artifact."
from __future__ import annotations
import os
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
from geoai_dataset_curation.image_construction.drive_artifact_retrieval import (
    GoogleDriveArtifactRetriever,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.image_construction.runtime_grid import (
    build_exact_raster_grid_from_study_area,
)
from geoai_dataset_curation.scene_preparation.study_area_loading import (
    load_study_area,
)


DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_FOLDER = "geoai-dataset-curation-loop1"
FILE_NAME = "komeh_sentinel2_2024_median.tif"
REMOTE_URI = f"drive://{DRIVE_FOLDER}/{FILE_NAME}"
LOCAL_PATH = Path("artifacts/live/loop1") / FILE_NAME


def main() -> None:
    "Retrieve the real GeoTIFF and verify its exact raster grid."
    study_area_path = Path(os.environ["GEOAI_STUDY_AREA_PATH"])
    study_area = load_study_area(
        path=study_area_path,
        study_area_id="komeh-study-area",
        source_id="padena_aoi",
    )

    approved_grid = build_exact_raster_grid_from_study_area(
        study_area=study_area,
        target_crs="EPSG:32639",
        pixel_size=10.0,
    )

    credentials, _ = google.auth.default(scopes=[DRIVE_SCOPE])

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    retriever = GoogleDriveArtifactRetriever(drive_service)

    request = RasterArtifactRetrievalRequest(
        artifact=RemoteRasterArtifact(
            uri=REMOTE_URI,
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=LOCAL_PATH,
    )

    print(f"Remote URI: {REMOTE_URI}")
    print(f"Local path: {LOCAL_PATH}")
    print(f"Approved grid ID: {build_raster_grid_id(approved_grid)}")
    print()
    print("Retrieving and verifying raster artifact...")

    result = retrieve_and_verify_raster_artifact(
        retriever=retriever,
        request=request,
        approved_grid=approved_grid,
    )

    metadata = result.metadata
    verification = result.grid_verification
    file_size = result.retrieval.local_path.stat().st_size

    print()
    print("Raster metadata:")
    print(f"Driver: {metadata.driver}")
    print(f"CRS: {metadata.crs}")
    print(f"Width: {metadata.width}")
    print(f"Height: {metadata.height}")
    print(f"Band count: {metadata.band_count}")
    print(f"Dtypes: {metadata.dtypes}")
    print(f"Transform: {tuple(metadata.transform)[:6]}")
    print(f"File size: {file_size} bytes")
    print()
    print("Exact-grid verification:")
    print(f"CRS match: {verification.crs_matches}")
    print(f"Width match: {verification.width_matches}")
    print(f"Height match: {verification.height_matches}")
    print(f"Transform match: {verification.transform_matches}")
    print(f"Overall match: {verification.matches}")
    print()
    print("PASS: Real raster artifact retrieval and verification succeeded.")


if __name__ == "__main__":
    main()