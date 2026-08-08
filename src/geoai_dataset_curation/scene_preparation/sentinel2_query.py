"Construction of provider-neutral Sentinel-2 scene queries"
from typing import cast
import geopandas as gpd
from shapely.geometry import mapping
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineSceneQuery,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneSelectionRequest,
    StudyAreaSpec,
)
from geoai_dataset_curation.scene_preparation.study_area_validation import (
    validate_study_area,
)
from geoai_dataset_curation.scene_preparation.validation import (
    validate_scene_selection_request,
)
from shapely.geometry.base import BaseGeometry


EARTH_ENGINE_QUERY_CRS = "EPSG:4326"


def build_sentinel2_scene_query(
    *,
    study_area: StudyAreaSpec,
    request: SceneSelectionRequest,
) -> EarthEngineSceneQuery:
    "Build one validated Earth Engine Sentinel-2 scene query"
    study_area_errors = validate_study_area(study_area)
    request_errors = validate_scene_selection_request(request)

    errors = study_area_errors + request_errors

    if request.source_id != study_area.source_id:
        errors += (
            "request.source_id must match study_area.source_id",
        )

    if errors:
        raise ValueError(
            "Cannot build Sentinel-2 scene query: "
            + "; ".join(errors)
        )

    geometry_series = gpd.GeoSeries(
        [study_area.geometry],
        crs=study_area.crs,
    )

    try:
        geographic_geometry = geometry_series.to_crs(
            EARTH_ENGINE_QUERY_CRS
        ).iloc[0]
    except Exception as error:
        raise ValueError(
            "Study-area geometry could not be transformed "
            "to EPSG:4326."
        ) from error

    if not isinstance(geographic_geometry, BaseGeometry):
        raise ValueError(
            "Study-area transformation produced no geometry."
        )

    aoi_geojson = cast(
        dict[str, object],
        mapping(geographic_geometry),
    )

    return EarthEngineSceneQuery(
        collection_id=request.collection,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat(),
        aoi_geojson=aoi_geojson,
        maximum_cloud_cover=request.max_cloud_cover,
    )