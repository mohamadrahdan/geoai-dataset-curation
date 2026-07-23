from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.validation import load_vector_file


def test_load_vector_file_reads_geospatial_data(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.geojson"

    expected = gpd.GeoDataFrame(
        {
            "source_id": ["sample_polygon"],
            "geometry": [
                Polygon(
                    [
                        (0, 0),
                        (1, 0),
                        (1, 1),
                        (0, 1),
                        (0, 0),
                    ]
                )
            ],
        },
        crs="EPSG:4326",
    )

    expected.to_file(source_path, driver="GeoJSON")
    loaded = load_vector_file(source_path)

    assert len(loaded) == 1
    assert loaded.crs is not None
    assert loaded.crs.to_epsg() == 4326
    assert loaded.geometry.geom_type.iloc[0] == "Polygon"