"Geometry helpers for exact raster grids"
from dataclasses import dataclass
from geoai_dataset_curation.image_construction.contracts import (RasterGridSpec)
from geoai_dataset_curation.image_construction.validation import (validate_exact_raster_grid_spec)


@dataclass(frozen=True)
class RasterBounds:
    "Spatial bounds derived from one exact north-up raster grid"
    left: float
    bottom: float
    right: float
    top: float

    @property
    def as_tuple(self) -> tuple[float, float, float, float]:
        "Return bounds in left, bottom, right, top order"
        return (
            self.left,
            self.bottom,
            self.right,
            self.top,
        )


def derive_raster_bounds(grid: RasterGridSpec) -> RasterBounds:
    "Derive exact bounds from one validated north-up raster grid"
    errors = validate_exact_raster_grid_spec(grid)
    if errors:
        joined_errors = "; ".join(errors)
        raise ValueError(
            f"Cannot derive raster bounds from an invalid grid: "
            f"{joined_errors}"
        )

    transform = grid.transform

    if transform is None:
        raise ValueError(
            "Cannot derive raster bounds without an affine transform."
        )

    left = transform.c
    top = transform.f
    right = left + (grid.width * transform.a)
    bottom = top + (grid.height * transform.e)

    return RasterBounds(
        left=left,
        bottom=bottom,
        right=right,
        top=top,
    )