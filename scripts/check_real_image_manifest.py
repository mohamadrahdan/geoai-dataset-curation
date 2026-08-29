"Build the final manifest for the real Loop 1 Sentinel-2 image artifact."
from __future__ import annotations
import json
import os
from datetime import date
from pathlib import Path
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RemoteRasterArtifact,
    RetrievedRasterArtifact,
)
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
)
from geoai_dataset_curation.image_construction.earth_engine_sdk_provider import (
    EarthEngineSdkProvider,
)
from geoai_dataset_curation.image_construction.earth_engine_sdk_runtime import (
    EarthEngineSdkRuntime,
)
from geoai_dataset_curation.image_construction.earth_engine_service import (
    EarthEngineService,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)
from geoai_dataset_curation.image_construction.raster_grid_verification import (
    verify_raster_against_grid,
)
from geoai_dataset_curation.image_construction.real_image_manifest import (
    create_complete_real_image_manifest,
    real_image_manifest_to_dict,
)
from geoai_dataset_curation.image_construction.runtime_grid import (
    build_exact_raster_grid_from_study_area,
)
from geoai_dataset_curation.image_construction.runtime_input import (
    build_real_image_runtime_input,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneCandidate,
    ScenePreparationResult,
)


DRIVE_FOLDER = "geoai-dataset-curation-loop1"
OUTPUT_NAME = "komeh_sentinel2_2024_median"
FILE_NAME = f"{OUTPUT_NAME}.tif"
REMOTE_URI = f"drive://{DRIVE_FOLDER}/{FILE_NAME}"
LOCAL_PATH = Path("artifacts/live/loop1") / FILE_NAME
MANIFEST_PATH = Path("artifacts/live/loop1") / f"{OUTPUT_NAME}.manifest.json"


def main() -> None:
    "Build, validate, and serialize the real-image manifest."
    project_id = os.environ["GEOAI_EE_PROJECT_ID"]
    study_area_path = Path(os.environ["GEOAI_STUDY_AREA_PATH"])
    export_task_id = os.environ["GEOAI_EE_EXPORT_TASK_ID"].strip()

    if not export_task_id:
        raise ValueError("GEOAI_EE_EXPORT_TASK_ID must not be empty.")
    if not LOCAL_PATH.is_file():
        raise FileNotFoundError(
            f"Retrieved raster artifact does not exist: {LOCAL_PATH}"
        )
    runtime_input = build_real_image_runtime_input(
        study_area_path=study_area_path,
        study_area_id="komeh-study-area",
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B2", "B3", "B4", "B8"),
        max_cloud_cover=20.0,
    )
    runtime = EarthEngineSdkRuntime()
    runtime.initialize_with_persistent_credentials(
        project_id=project_id,
        api_endpoint=None,
    )

    provider = EarthEngineSdkProvider()
    service = EarthEngineService(provider)
    scenes = service.search_sentinel2_scenes(runtime_input.scene_query)

    if not scenes:
        raise RuntimeError("No Sentinel-2 scenes were returned.")
    scene_candidates = tuple(
        SceneCandidate(
            scene_id=scene.scene_id,
            acquisition_date=date.fromisoformat(scene.acquisition_date),
            cloud_cover=scene.cloud_cover,
            collection=runtime_input.selection_request.collection,
            available_bands=(
                *runtime_input.selection_request.required_bands,
                "SCL",
            ),
        )
        for scene in scenes
    )
    scene_preparation = ScenePreparationResult(
        source_id=runtime_input.selection_request.source_id,
        candidate_count=len(scene_candidates),
        selected_count=len(scene_candidates),
        rejected_count=0,
        selected_scenes=scene_candidates,
    )
    composite_request = EarthEngineCompositeRequest(
        scene_ids=tuple(scene.scene_id for scene in scenes),
        bands=runtime_input.selection_request.required_bands,
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=EarthEngineAggregationMethod.MEDIAN,
    )
    composite = service.build_composite(composite_request)
    approved_grid = build_exact_raster_grid_from_study_area(
        study_area=runtime_input.study_area,
        target_crs="EPSG:32639",
        pixel_size=10.0,
    )
    inspected_metadata = inspect_raster_artifact(LOCAL_PATH)
    verification = verify_raster_against_grid(
        inspected_metadata,
        approved_grid,
    )

    if not verification.matches:
        raise RuntimeError(
            "Local raster artifact does not match the approved exact grid."
        )
    retrieved_artifact = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri=REMOTE_URI,
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=LOCAL_PATH,
    )
    export_request = EarthEngineExportRequest(
        image=composite,
        output_name=OUTPUT_NAME,
        grid=approved_grid,
        destination=EarthEngineExportDestination.DRIVE,
        destination_folder=DRIVE_FOLDER,
    )
    export_task = EarthEngineExportTaskReference(
        task_id=export_task_id,
    )

    manifest = create_complete_real_image_manifest(
        scene_preparation=scene_preparation,
        composite_request=composite_request,
        export_request=export_request,
        export_task=export_task,
        retrieved_artifact=retrieved_artifact,
        inspected_metadata=inspected_metadata,
        approved_grid=approved_grid,
    )
    payload = real_image_manifest_to_dict(manifest)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(f"Source ID: {manifest.source_id}")
    print(f"Output name: {manifest.output_name}")
    print(f"Scene count: {len(scene_candidates)}")
    print(f"Artifact URI: {manifest.artifact_uri}")
    print(f"Artifact path: {LOCAL_PATH}")
    print(f"Manifest path: {MANIFEST_PATH}")
    print()
    print("Artifact:")
    print(f"Driver: {payload['artifact']['driver']}")
    print(
        "Dimensions: "
        f"{payload['artifact']['width']} x "
        f"{payload['artifact']['height']}"
    )
    print(f"Band count: {payload['artifact']['band_count']}")
    print(f"Dtypes: {payload['artifact']['dtypes']}")
    print(f"File size: {payload['artifact']['file_size_bytes']} bytes")
    print()
    print("Composite provenance:")
    print(f"Scenes: {len(payload['provenance']['scenes'])}")
    print(f"Bands: {payload['provenance']['bands']}")
    print(f"Aggregation: {payload['provenance']['aggregation_method']}")
    print(f"Cloud mask band: {payload['provenance']['cloud_mask_band']}")
    print(
        "Excluded SCL classes: "
        f"{payload['provenance']['excluded_cloud_mask_classes']}"
    )
    print()
    print("Exact grid:")
    print(f"Grid ID: {payload['grid']['grid_id']}")
    print(f"CRS: {payload['grid']['crs']}")
    print(
        "Dimensions: "
        f"{payload['grid']['width']} x "
        f"{payload['grid']['height']}"
    )
    print(f"Transform: {payload['grid']['transform']}")
    print()
    print("Export trace:")
    print(f"Task ID: {payload['export_trace']['task_id']}")
    print(f"Destination: {payload['export_trace']['destination']}")
    print(
        "Destination folder: "
        f"{payload['export_trace']['destination_folder']}"
    )
    print(
        "Remote URI: "
        f"{payload['export_trace']['remote_artifact_uri']}"
    )
    print()
    print("PASS: Real-image manifest was generated successfully.")


if __name__ == "__main__":
    main()