"Validation rules for Earth Engine provider requests"
from datetime import date
from math import isfinite
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineSceneQuery,
)
from geoai_dataset_curation.image_construction.validation import (
    validate_exact_raster_grid_spec,
)
from geoai_dataset_curation.image_construction.cloud_mask_validation import (
    validate_sentinel2_cloud_mask_spec,
)


def _is_iso_date(value: str) -> bool:
    "Return whether one value is a valid ISO calendar date"
    try:
        date.fromisoformat(value)
    except ValueError:
        return False

    return True


def validate_earth_engine_scene_query(
    query: EarthEngineSceneQuery,
) -> tuple[str, ...]:
    "Return validation errors for one Sentinel-2 scene query"
    errors: list[str] = []

    if not query.collection_id.strip():
        errors.append("collection_id must not be empty.")

    start_is_valid = _is_iso_date(query.start_date)
    end_is_valid = _is_iso_date(query.end_date)

    if not start_is_valid:
        errors.append("start_date must be a valid ISO date.")

    if not end_is_valid:
        errors.append("end_date must be a valid ISO date.")

    if (
        start_is_valid
        and end_is_valid
        and date.fromisoformat(query.start_date)
        > date.fromisoformat(query.end_date)
    ):
        errors.append("start_date must not be after end_date.")

    if query.aoi_geojson.get("type") not in {
        "Polygon",
        "MultiPolygon",
    }:
        errors.append(
            "aoi_geojson.type must be Polygon or MultiPolygon."
        )

    if "coordinates" not in query.aoi_geojson:
        errors.append(
            "aoi_geojson must contain coordinates."
        )

    if not isfinite(query.maximum_cloud_cover):
        errors.append(
            "maximum_cloud_cover must be finite."
        )
    elif not 0.0 <= query.maximum_cloud_cover <= 100.0:
        errors.append(
            "maximum_cloud_cover must be between 0 and 100."
        )

    return tuple(errors)


def validate_earth_engine_composite_request(
    request: EarthEngineCompositeRequest,
) -> tuple[str, ...]:
    "Return validation errors for one composite request"
    errors: list[str] = []

    if not request.scene_ids:
        errors.append(
            "scene_ids must contain at least one scene."
        )

    if len(set(request.scene_ids)) != len(request.scene_ids):
        errors.append(
            "scene_ids must not contain duplicates."
        )

    if any(not scene_id.strip() for scene_id in request.scene_ids):
        errors.append(
            "scene_ids must not contain empty values."
        )

    if not request.bands:
        errors.append(
            "bands must contain at least one band."
        )

    if len(set(request.bands)) != len(request.bands):
        errors.append(
            "bands must not contain duplicates."
        )

    if any(not band.strip() for band in request.bands):
        errors.append(
            "bands must not contain empty values."
        )

    errors.extend(
        validate_sentinel2_cloud_mask_spec(
            request.cloud_mask
        )
    )

    return tuple(errors)


def validate_earth_engine_export_request(
    request: EarthEngineExportRequest,
) -> tuple[str, ...]:
    "Return validation errors for one exact-grid export request"
    errors: list[str] = []

    if not request.image.image_id.strip():
        errors.append("image.image_id must not be empty.")

    if not request.output_name.strip():
        errors.append("output_name must not be empty.")

    errors.extend(
        validate_exact_raster_grid_spec(request.grid)
    )

    return tuple(errors)