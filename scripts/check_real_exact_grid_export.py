"Live production-style Sentinel-2 composite export on the exact study-area grid."
from __future__ import annotations
import os
import time
from datetime import date
from pathlib import Path
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
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
from geoai_dataset_curation.image_construction.grid_geometry import (
    derive_raster_bounds,
)
from geoai_dataset_curation.image_construction.runtime_grid import (
    build_exact_raster_grid_from_study_area,
)
from geoai_dataset_curation.image_construction.runtime_input import (
    build_real_image_runtime_input,
)

EXPORT_FOLDER = "geoai-dataset-curation-loop1"
EXPORT_NAME = "komeh_sentinel2_2024_median"
POLL_INTERVAL_SECONDS = 10.0
MAX_POLLS = 180


def main() -> None:
    "Build and export the real Sentinel-2 composite on the exact raster grid."
    project_id = os.environ["GEOAI_EE_PROJECT_ID"]
    study_area_path = Path(os.environ["GEOAI_STUDY_AREA_PATH"])

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

    composite_request = EarthEngineCompositeRequest(
        scene_ids=tuple(scene.scene_id for scene in scenes),
        bands=runtime_input.selection_request.required_bands,
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=EarthEngineAggregationMethod.MEDIAN,
    )

    composite = service.build_composite(composite_request)

    grid = build_exact_raster_grid_from_study_area(
        study_area=runtime_input.study_area,
        target_crs="EPSG:32639",
        pixel_size=10.0,
    )

    bounds = derive_raster_bounds(grid)

    export_request = EarthEngineExportRequest(
        image=composite,
        output_name=EXPORT_NAME,
        grid=grid,
        destination=EarthEngineExportDestination.DRIVE,
        destination_folder=EXPORT_FOLDER,
    )

    print(f"Project: {project_id}")
    print(f"Study area: {runtime_input.study_area.study_area_id}")
    print(f"Scene count: {len(scenes)}")
    print(f"Composite: {composite.image_id}")
    print(f"Bands: {', '.join(composite_request.bands)}")
    print(f"Grid CRS: {grid.crs}")
    print(f"Grid dimensions: {grid.width} x {grid.height}")
    print(f"Pixel count: {grid.width * grid.height}")
    print(f"Grid bounds: {bounds.as_tuple}")
    print(f"Transform: {grid.transform.as_tuple if grid.transform else None}")
    print(f"Drive folder: {EXPORT_FOLDER}")
    print(f"Output name: {EXPORT_NAME}")

    print()
    print("Starting Earth Engine export...")

    export_task = service.start_export(export_request)

    print(f"Export task ID: {export_task.task_id}")

    for poll_number in range(1, MAX_POLLS + 1):
        status = service.get_export_status(export_task)
        print(f"Poll {poll_number}: {status.state.value}")
        if status.succeeded:
            print()
            print("PASS: Real exact-grid Earth Engine export completed.")
            print(f"Task ID: {export_task.task_id}")
            print(f"Drive folder: {EXPORT_FOLDER}")
            print(f"File prefix: {EXPORT_NAME}")
            return
        if status.is_terminal:
            raise RuntimeError(
                "Earth Engine export terminated with "
                f"state {status.state.value!r}: "
                f"{status.error_message or 'no error message'}"
            )
        if poll_number < MAX_POLLS:
            time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(
        "Earth Engine export did not complete within the polling window."
    )


if __name__ == "__main__":
    main()