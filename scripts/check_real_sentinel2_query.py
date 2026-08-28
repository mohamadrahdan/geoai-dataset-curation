"Live check for real Sentinel-2 discovery and composite construction"
from __future__ import annotations
import os
from datetime import date
from pathlib import Path
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
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
from geoai_dataset_curation.image_construction.runtime_input import (
    build_real_image_runtime_input,
)


def main() -> None:
    "Discover real Sentinel-2 scenes and build the production composite"
    project_id = os.environ["GEOAI_EE_PROJECT_ID"]
    study_area_path = Path(
        os.environ["GEOAI_STUDY_AREA_PATH"]
    )

    runtime_input = build_real_image_runtime_input(
        study_area_path=study_area_path,
        study_area_id="komeh-study-area",
        source_id="padena_aoi",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        max_cloud_cover=20.0,
    )

    runtime = EarthEngineSdkRuntime()
    runtime.initialize_with_persistent_credentials(
        project_id=project_id,
        api_endpoint=None,
    )
    provider = EarthEngineSdkProvider()
    service = EarthEngineService(provider)
    scenes = service.search_sentinel2_scenes(
        runtime_input.scene_query
    )

    if not scenes:
        raise RuntimeError(
            "No Sentinel-2 scenes were returned "
            "for the real study area."
        )

    print(f"Project: {project_id}")
    print(
        "Study area: "
        f"{runtime_input.study_area.study_area_id}"
    )
    print(f"CRS: {runtime_input.study_area.crs}")
    print(
        "Date range: "
        "2024-01-01 -> 2024-12-31"
    )
    print("Maximum scene cloud cover: 20%")
    print(f"Returned scene count: {len(scenes)}")

    cloud_mask = Sentinel2CloudMaskSpec()
    composite_request = EarthEngineCompositeRequest(
        scene_ids=tuple(
            scene.scene_id
            for scene in scenes
        ),
        bands=runtime_input.selection_request.required_bands,
        cloud_mask=cloud_mask,
        aggregation_method=EarthEngineAggregationMethod.MEDIAN,
    )
    composite = service.build_composite(
        composite_request
    )

    print()
    print("Composite configuration:")
    print(
        f"Scene count: "
        f"{len(composite_request.scene_ids)}"
    )
    print(
        "Bands: "
        + ", ".join(composite_request.bands)
    )
    print(
        f"SCL mask band: "
        f"{composite_request.cloud_mask.scl_band}"
    )
    print(
        "Excluded SCL classes: "
        + ", ".join(
            str(class_value)
            for class_value
            in composite_request.cloud_mask.excluded_scl_classes
        )
    )
    print(
        "Aggregation: "
        f"{composite_request.aggregation_method.value}"
    )
    print(
        f"Composite image reference: "
        f"{composite.image_id}"
    )

    print()
    print(
        "PASS: Real Sentinel-2 production composite "
        "was constructed successfully."
    )


if __name__ == "__main__":
    main()