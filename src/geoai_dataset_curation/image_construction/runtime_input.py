"Runtime wiring for real image-construction inputs"
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineSceneQuery,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneSelectionRequest,
    StudyAreaSpec,
)
from geoai_dataset_curation.scene_preparation.sentinel2_query import (
    build_sentinel2_scene_query,
)
from geoai_dataset_curation.scene_preparation.study_area_loading import (
    load_study_area,
)


@dataclass(frozen=True)
class RealImageRuntimeInput:
    "Prepared runtime input for one real image-construction execution"
    study_area: StudyAreaSpec
    selection_request: SceneSelectionRequest
    scene_query: EarthEngineSceneQuery


def build_real_image_runtime_input(
    *,
    study_area_path: str | Path,
    study_area_id: str,
    source_id: str,
    start_date: date,
    end_date: date,
    collection: str,
    required_bands: tuple[str, ...],
    max_cloud_cover: float,
) -> RealImageRuntimeInput:
    "Load one real study area and build its validated scene query"
    study_area = load_study_area(
        path=study_area_path,
        study_area_id=study_area_id,
        source_id=source_id,
    )

    selection_request = SceneSelectionRequest(
        source_id=source_id,
        start_date=start_date,
        end_date=end_date,
        collection=collection,
        required_bands=required_bands,
        max_cloud_cover=max_cloud_cover,
    )

    scene_query = build_sentinel2_scene_query(
        study_area=study_area,
        request=selection_request,
    )

    return RealImageRuntimeInput(
        study_area=study_area,
        selection_request=selection_request,
        scene_query=scene_query,
    )