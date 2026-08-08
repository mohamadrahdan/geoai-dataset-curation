"Contracts for Sentinel-2 scene preparation"
from dataclasses import dataclass
from datetime import date
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class StudyAreaSpec:
    "Spatial contract for one region-independent study area"
    study_area_id: str
    source_id: str
    crs: str
    geometry: BaseGeometry


@dataclass(frozen=True)
class SceneSelectionRequest:
    "Selection criteria for preparing Sentinel-2 scenes"
    source_id: str
    start_date: date
    end_date: date
    collection: str
    required_bands: tuple[str, ...]
    max_cloud_cover: float


@dataclass(frozen=True)
class SceneCandidate:
    "One Sentinel-2 scene considered for dataset construction"
    scene_id: str
    acquisition_date: date
    cloud_cover: float
    collection: str
    available_bands: tuple[str, ...]


@dataclass(frozen=True)
class ScenePreparationResult:
    "Summary of one scene-preparation run"
    source_id: str
    candidate_count: int
    selected_count: int
    rejected_count: int
    selected_scenes: tuple[SceneCandidate, ...]

    @property
    def has_selected_scenes(self) -> bool:
        "Return whether at least one scene was selected"
        return self.selected_count > 0