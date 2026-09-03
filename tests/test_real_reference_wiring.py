from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.label_rasterization import (
    RealReferenceSourceConfig,
    wire_real_reference_source,
    wire_real_reference_sources,
)
from geoai_dataset_curation.label_rasterization.geometry_repair import (
    GeometryRepairSummary,
    repair_invalid_reference_geometries,
)
from geoai_dataset_curation.validation import (
    validate_source,
    validate_source_metadata,
)


def write_reference_file(
    path: Path,
    *,
    crs: str = "EPSG:4326",
) -> None:
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon(
                    [
                        (51.0, 30.0),
                        (51.01, 30.0),
                        (51.01, 30.01),
                        (51.0, 30.01),
                        (51.0, 30.0),
                    ]
                )
            ]
        },
        crs=crs,
    )
    frame.to_file(
        path,
        driver="GeoJSON",
    )


def test_real_reference_source_is_loaded_and_reprojected(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "positive.geojson"
    write_reference_file(source_path)
    config = RealReferenceSourceConfig(
        source_id="positive-reference",
        path=source_path,
        supervision=SupervisionKind.POSITIVE_REFERENCE,
    )
    result = wire_real_reference_source(
        config=config,
        target_crs="EPSG:32639",
    )
    assert result.source_id == "positive-reference"
    assert result.source_crs == "EPSG:4326"
    assert result.target_crs == "EPSG:32639"
    assert result.feature_count == 1
    assert (
        result.vector_source.supervision
        == SupervisionKind.POSITIVE_REFERENCE
    )
    assert len(result.vector_source.geometries) == 1
    assert result.repair_summary.feature_count == 1
    assert result.repair_summary.repaired_count == 0
    assert result.repair_summary.unchanged_count == 1


def test_missing_reference_file_is_rejected(
    tmp_path: Path,
) -> None:
    config = RealReferenceSourceConfig(
        source_id="positive-reference",
        path=tmp_path / "missing.geojson",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
    )
    try:
        wire_real_reference_source(
            config=config,
            target_crs="EPSG:32639",
        )
    except FileNotFoundError as error:
        assert "Reference source does not exist" in str(error)
    else:
        raise AssertionError(
            "Missing reference source was not rejected."
        )


def test_multiple_reference_sources_preserve_supervision(
    tmp_path: Path,
) -> None:
    positive_path = tmp_path / "positive.geojson"
    negative_path = tmp_path / "negative.geojson"
    write_reference_file(positive_path)
    write_reference_file(negative_path)
    configs = (
        RealReferenceSourceConfig(
            source_id="positive-reference",
            path=positive_path,
            supervision=SupervisionKind.POSITIVE_REFERENCE,
        ),
        RealReferenceSourceConfig(
            source_id="negative-reference",
            path=negative_path,
            supervision=SupervisionKind.NEGATIVE_REFERENCE,
        ),
    )
    results = wire_real_reference_sources(
        configs=configs,
        target_crs="EPSG:32639",
    )
    assert len(results) == 2
    assert (
        results[0].vector_source.supervision
        == SupervisionKind.POSITIVE_REFERENCE
    )
    assert (
        results[1].vector_source.supervision
        == SupervisionKind.NEGATIVE_REFERENCE
    )


def test_invalid_reference_geometry_is_repaired_before_wiring(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "invalid.geojson"
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon(
                    [
                        (51.0, 30.0),
                        (51.01, 30.01),
                        (51.0, 30.01),
                        (51.01, 30.0),
                        (51.0, 30.0),
                    ]
                )
            ]
        },
        crs="EPSG:4326",
    )
    frame.to_file(
        source_path,
        driver="GeoJSON",
    )
    config = RealReferenceSourceConfig(
        source_id="positive-reference",
        path=source_path,
        supervision=SupervisionKind.POSITIVE_REFERENCE,
    )
    result = wire_real_reference_source(
        config=config,
        target_crs="EPSG:32639",
    )
    assert result.repair_summary.repaired_count == 1
    assert all(
        geometry.is_valid
        for geometry in result.vector_source.geometries
    )