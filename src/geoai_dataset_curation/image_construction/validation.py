"Validation rules for image-construction requests"

from math import isclose, isfinite

from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    ImageConstructionRequest,
    RasterGridSpec,
)


def validate_affine_transform_spec(
    transform: AffineTransformSpec,
    *,
    pixel_size_x: float,
    pixel_size_y: float,
) -> tuple[str, ...]:
    "Return validation errors for one north-up affine transform"

    errors: list[str] = []

    coefficients = transform.as_tuple

    if not all(isfinite(value) for value in coefficients):
        errors.append("grid.transform coefficients must be finite.")

    if transform.a == 0:
        errors.append("grid.transform.a must not be zero.")

    if transform.e == 0:
        errors.append("grid.transform.e must not be zero.")

    if transform.b != 0:
        errors.append(
            "grid.transform.b must be zero for a north-up raster grid."
        )

    if transform.d != 0:
        errors.append(
            "grid.transform.d must be zero for a north-up raster grid."
        )

    if not isclose(
        abs(transform.a),
        pixel_size_x,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        errors.append(
            "grid.transform.a must match grid.pixel_size_x."
        )

    if not isclose(
        abs(transform.e),
        pixel_size_y,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        errors.append(
            "grid.transform.e must match grid.pixel_size_y."
        )

    return tuple(errors)


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

    if grid.transform is not None:
        errors.extend(
            validate_affine_transform_spec(
                grid.transform,
                pixel_size_x=grid.pixel_size_x,
                pixel_size_y=grid.pixel_size_y,
            )
        )

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