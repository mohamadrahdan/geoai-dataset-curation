from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.validation import validate_vector_file


def test_validate_vector_file_loads_and_validates_source(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.geojson"

    frame = gpd.GeoDataFrame(
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

    frame.to_file(source_path, driver="GeoJSON")

    summary = validate_vector_file(
        source_id="sample_source",
        path=source_path,
    )

    assert summary.source_id == "sample_source"
    assert summary.feature_count == 1
    assert summary.valid_feature_count == 1
    assert summary.invalid_feature_count == 0
    assert summary.is_valid is True
    assert summary.issues == ()