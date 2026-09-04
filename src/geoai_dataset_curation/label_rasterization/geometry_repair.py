"Controlled repair of invalid reference geometries"
from dataclasses import dataclass
import geopandas as gpd
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry


SUPPORTED_POLYGON_TYPES = {
    "Polygon",
    "MultiPolygon",
}


@dataclass(frozen=True)
class GeometryRepairSummary:
    "Summary of one controlled geometry-repair operation"
    feature_count: int
    repaired_count: int
    unchanged_count: int


def _extract_polygonal_geometry(
    geometry: BaseGeometry,
) -> BaseGeometry:
    "Return polygonal content from one repaired geometry"
    if geometry.geom_type in SUPPORTED_POLYGON_TYPES:
        return geometry
    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []
        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)
            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)
        if not polygons:
            raise ValueError(
                "Geometry repair produced no polygonal geometry."
            )
        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)
    raise ValueError(
        "Geometry repair produced an unsupported geometry type: "
        f"{geometry.geom_type}"
    )


def repair_invalid_reference_geometries(
    frame: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, GeometryRepairSummary]:
    "Repair invalid polygon geometries while preserving valid features"
    repaired = frame.copy()
    repaired_count = 0
    for index, geometry in repaired.geometry.items():
        if geometry is None or geometry.is_empty:
            continue
        if geometry.is_valid:
            continue
        fixed = _extract_polygonal_geometry(
            make_valid(geometry)
        )
        if not fixed.is_valid:
            raise ValueError(
                f"Geometry remains invalid after repair: feature {index}"
            )
        repaired.at[index, "geometry"] = fixed
        repaired_count += 1

    return (
        repaired,
        GeometryRepairSummary(
            feature_count=len(repaired),
            repaired_count=repaired_count,
            unchanged_count=len(repaired) - repaired_count,
        ),
    )