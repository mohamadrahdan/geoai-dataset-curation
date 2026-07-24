"Contracts for Sentinel-2 scene preparation"

from dataclasses import dataclass
from datetime import date


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