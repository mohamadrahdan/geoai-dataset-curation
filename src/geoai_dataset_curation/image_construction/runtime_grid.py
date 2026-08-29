"Runtime construction of exact raster grids from study areas"
from __future__ import annotations
from math import ceil, floor
import geopandas as gpd
from typing import cast
from shapely.geometry.base import BaseGeometry
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    StudyAreaSpec,
)


def build_exact_raster_grid_from_study_area(
    *,
    study_area: StudyAreaSpec,
    target_crs: str,
    pixel_size: float,
) -> RasterGridSpec:
    "Build a north-up exact raster grid covering one study area"
    if not target_crs.strip():
        raise ValueError("target_crs must not be empty.")

    if pixel_size <= 0:
        raise ValueError("pixel_size must be greater than zero.")

    geometry_series = gpd.GeoSeries(
        [study_area.geometry],
        crs=study_area.crs,
    )

    try:
        projected_geometry = cast(
            BaseGeometry,
            geometry_series.to_crs(
                target_crs
            ).iloc[0],
        )
    except Exception as error:
        raise ValueError(
            "Study-area geometry could not be transformed "
            "to the target raster CRS."
        ) from error

    min_x, min_y, max_x, max_y = (projected_geometry.bounds)

    left = (floor(min_x / pixel_size) * pixel_size)
    right = (ceil(max_x / pixel_size) * pixel_size)
    bottom = (floor(min_y / pixel_size) * pixel_size)
    top = (ceil(max_y / pixel_size) * pixel_size)

    width = int(round((right - left) / pixel_size))
    height = int(round((top - bottom) / pixel_size))

    transform = AffineTransformSpec(
        a=pixel_size,
        b=0.0,
        c=left,
        d=0.0,
        e=-pixel_size,
        f=top,
    )

    return RasterGridSpec(
        crs=target_crs,
        width=width,
        height=height,
        pixel_size_x=pixel_size,
        pixel_size_y=pixel_size,
        transform=transform,
    )