"Loading of region-independent study-area geometries"
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias
import geopandas as gpd
from geopandas import GeoDataFrame
from geoai_dataset_curation.scene_preparation.contracts import (StudyAreaSpec)


StudyAreaReader: TypeAlias = Callable[[Path], GeoDataFrame]


class StudyAreaLoadingError(RuntimeError):
    "Raised when a study-area source cannot be loaded"


def load_study_area(
    *,
    path: str | Path,
    study_area_id: str,
    source_id: str,
    reader: StudyAreaReader = gpd.read_file,
) -> StudyAreaSpec:
    "Load one spatial source and create a study-area contract"
    source_path = Path(path)

    try:
        frame = reader(source_path)
    except Exception as error:
        raise StudyAreaLoadingError(
            f"Study-area source could not be loaded: {source_path}"
        ) from error

    if frame.empty:
        raise StudyAreaLoadingError(
            "Study-area source must contain at least one feature."
        )

    try:
        geometry = frame.geometry.union_all()
    except Exception as error:
        raise StudyAreaLoadingError(
            "Study-area geometries could not be combined."
        ) from error

    crs = (
        frame.crs.to_string()
        if frame.crs is not None
        else ""
    )

    return StudyAreaSpec(
        study_area_id=study_area_id,
        source_id=source_id,
        crs=crs,
        geometry=geometry,
    )