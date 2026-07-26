"Validation rules for image-construction requests"

from geoai_dataset_curation.image_construction.contracts import (
    ImageConstructionRequest,
    RasterGridSpec,
)


def validate_raster_grid_spec(
    grid: RasterGridSpec,
) -> tuple[str, ...]:
    "Return all detected validation errors for one raster-grid specification"

    errors: list[str] = []
    if not grid.crs.strip():
        errors.append("grid.crs must not be empty.")

    if grid.width <= 0:
        errors.append("grid.width must be greater than zero.")

    if grid.height <= 0:
        errors.append("grid.height must be greater than zero.")

    if grid.pixel_size_x <= 0:
        errors.append("grid.pixel_size_x must be greater than zero.")

    if grid.pixel_size_y <= 0:
        errors.append("grid.pixel_size_y must be greater than zero.")

    return tuple(errors)


def validate_image_construction_request(
    request: ImageConstructionRequest,
) -> tuple[str, ...]:
    "Return all detected validation errors for one construction request"

    errors: list[str] = []

    if not request.source_id.strip():
        errors.append("source_id must not be empty")

    if not request.scene_ids:
        errors.append("scene_ids must contain at least one scene")

    if len(set(request.scene_ids)) != len(request.scene_ids):
        errors.append("scene_ids must not contain duplicates")

    if not request.bands:
        errors.append("bands must contain at least one band")

    if len(set(request.bands)) != len(request.bands):
        errors.append("bands must not contain duplicates")

    if not request.output_name.strip():
        errors.append("output_name must not be empty")

    errors.extend(validate_raster_grid_spec(request.grid))

    return tuple(errors)