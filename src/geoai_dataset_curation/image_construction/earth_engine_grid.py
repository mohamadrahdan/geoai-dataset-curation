"Earth Engine export-grid serialization helpers"
from typing import Any
from geoai_dataset_curation.image_construction.contracts import (RasterGridSpec)
from geoai_dataset_curation.image_construction.grid_geometry import (derive_raster_bounds)
from geoai_dataset_curation.image_construction.validation import (validate_exact_raster_grid_spec)


def raster_grid_to_earth_engine_export_params(
    grid: RasterGridSpec,
) -> dict[str, Any]:
    "Convert one exact raster grid into Earth Engine export parameters"
    errors = validate_exact_raster_grid_spec(grid)

    if errors:
        joined_errors = "; ".join(errors)
        raise ValueError(
            f"Cannot serialize an invalid Earth Engine export grid: "
            f"{joined_errors}"
        )

    transform = grid.transform

    if transform is None:
        raise ValueError(
            "Cannot serialize Earth Engine export parameters "
            "without an affine transform."
        )

    bounds = derive_raster_bounds(grid)

    return {
        "crs": grid.crs,
        "crsTransform": list(transform.as_tuple),
        "dimensions": {
            "width": grid.width,
            "height": grid.height,
        },
        "bounds": {
            "left": bounds.left,
            "bottom": bounds.bottom,
            "right": bounds.right,
            "top": bounds.top,
        },
    }