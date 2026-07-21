"Input helpers for vector-source validation"

from pathlib import Path
import geopandas as gpd


def load_vector_file(path: Path) -> gpd.GeoDataFrame:
    "Load one vector file into a GeoDataFrame"

    return gpd.read_file(path)