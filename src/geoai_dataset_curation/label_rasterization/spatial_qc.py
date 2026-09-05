"Spatial quality control for vector supervision on an exact raster grid"
from dataclasses import dataclass
from typing import cast
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from rasterio.transform import array_bounds
from shapely.geometry import box
from geoai_dataset_curation.image_construction.contracts import RasterGridSpec
from geoai_dataset_curation.label_rasterization.contracts import LabelVectorSource


@dataclass(frozen=True)
class SourceSpatialQC:
    "Spatial rasterization QC summary for one vector source"
    source_id: str
    feature_count: int
    covered_pixel_count: int
    zero_pixel_feature_indices: tuple[int, ...]
    partially_outside_feature_indices: tuple[int, ...]
    disjoint_feature_indices: tuple[int, ...]

    @property
    def zero_pixel_feature_count(self) -> int:
        return len(self.zero_pixel_feature_indices)

    @property
    def partially_outside_feature_count(self) -> int:
        return len(self.partially_outside_feature_indices)

    @property
    def disjoint_feature_count(self) -> int:
        return len(self.disjoint_feature_indices)


def _grid_transform(grid: RasterGridSpec) -> Affine:
    if grid.transform is None:
        raise ValueError("Spatial QC requires an exact raster transform")
    return Affine(*grid.transform.as_tuple)


def _grid_footprint(grid: RasterGridSpec):
    transform = _grid_transform(grid)
    west, south, east, north = array_bounds(
        grid.height,
        grid.width,
        transform,
    )
    return box(west, south, east, north)


def validate_no_disjoint_geometries(
    source: LabelVectorSource,
    grid: RasterGridSpec,
) -> None:
    "Reject supervision geometries that are fully outside the target grid"
    footprint = _grid_footprint(grid)
    disjoint_indices = tuple(
        index
        for index, geometry in enumerate(source.geometries)
        if not geometry.intersects(footprint)
    )
    if disjoint_indices:
        raise ValueError(
            "Reference geometries are fully outside the target grid: "
            f"{source.source_id}: {disjoint_indices}"
        )


def analyze_source_spatial_qc(
    source: LabelVectorSource,
    grid: RasterGridSpec,
) -> SourceSpatialQC:
    "Measure the spatial contribution of one vector supervision source"
    transform = _grid_transform(grid)
    footprint = _grid_footprint(grid)
    source_mask = cast(
        np.ndarray,
        rasterize(
            ((geometry, 1) for geometry in source.geometries),
            out_shape=(grid.height, grid.width),
            transform=transform,
            fill=0,
            all_touched=False,
            dtype="uint8",
        ),
    )
    zero_pixel_indices: list[int] = []
    partial_indices: list[int] = []
    disjoint_indices: list[int] = []

    for index, geometry in enumerate(source.geometries):
        if not geometry.intersects(footprint):
            disjoint_indices.append(index)
        elif not footprint.covers(geometry):
            partial_indices.append(index)

        feature_mask = cast(
            np.ndarray,
            rasterize(
                ((geometry, 1),),
                out_shape=(grid.height, grid.width),
                transform=transform,
                fill=0,
                all_touched=False,
                dtype="uint8",
            ),
        )

        if not np.any(feature_mask):
            zero_pixel_indices.append(index)

    return SourceSpatialQC(
        source_id=source.source_id,
        feature_count=len(source.geometries),
        covered_pixel_count=int(np.count_nonzero(source_mask)),
        zero_pixel_feature_indices=tuple(zero_pixel_indices),
        partially_outside_feature_indices=tuple(partial_indices),
        disjoint_feature_indices=tuple(disjoint_indices),
    )


def compute_source_overlap_pixel_count(
    first: LabelVectorSource,
    second: LabelVectorSource,
    grid: RasterGridSpec,
) -> int:
    "Count raster pixels shared by two vector supervision sources"
    transform = _grid_transform(grid)
    first_mask = cast(
        np.ndarray,
        rasterize(
            ((geometry, 1) for geometry in first.geometries),
            out_shape=(grid.height, grid.width),
            transform=transform,
            fill=0,
            all_touched=False,
            dtype="uint8",
        ),
    )
    second_mask = cast(
        np.ndarray,
        rasterize(
            ((geometry, 1) for geometry in second.geometries),
            out_shape=(grid.height, grid.width),
            transform=transform,
            fill=0,
            all_touched=False,
            dtype="uint8",
        ),
    )
    return int(
        np.count_nonzero(
            first_mask.astype(bool)
            & second_mask.astype(bool)
        )
    )