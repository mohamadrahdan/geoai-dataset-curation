from math import inf
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    RasterGridSpec,
    validate_earth_engine_composite_request,
    validate_earth_engine_export_request,
    validate_earth_engine_scene_query,
    Sentinel2CloudMaskSpec,
)


def make_exact_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        ),
    )


def test_validate_earth_engine_scene_query_accepts_valid_query() -> None:
    query = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-06-01",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=20.0,
    )

    errors = validate_earth_engine_scene_query(query)
    assert errors == ()


def test_validate_earth_engine_scene_query_rejects_invalid_dates() -> None:
    query = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-13-01",
        end_date="not-a-date",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=20.0,
    )

    errors = validate_earth_engine_scene_query(query)
    assert "start_date must be a valid ISO date." in errors
    assert "end_date must be a valid ISO date." in errors


def test_validate_earth_engine_scene_query_rejects_reversed_date_range() -> None:
    query = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-09-30",
        end_date="2024-06-01",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=20.0,
    )

    errors = validate_earth_engine_scene_query(query)
    assert "start_date must not be after end_date." in errors


def test_validate_earth_engine_scene_query_rejects_invalid_aoi() -> None:
    query = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-06-01",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Point",
        },
        maximum_cloud_cover=20.0,
    )

    errors = validate_earth_engine_scene_query(query)

    assert (
        "aoi_geojson.type must be Polygon or MultiPolygon."
        in errors
    )
    assert "aoi_geojson must contain coordinates." in errors


def test_validate_earth_engine_scene_query_rejects_invalid_cloud_cover() -> None:
    above_range = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-06-01",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=101.0,
    )
    non_finite = EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-06-01",
        end_date="2024-09-30",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [],
        },
        maximum_cloud_cover=inf,
    )

    above_range_errors = validate_earth_engine_scene_query(
        above_range
    )
    non_finite_errors = validate_earth_engine_scene_query(
        non_finite
    )

    assert (
        "maximum_cloud_cover must be between 0 and 100."
        in above_range_errors
    )
    assert (
        "maximum_cloud_cover must be finite."
        in non_finite_errors
    )


def test_validate_earth_engine_composite_request_accepts_valid_request() -> None:
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-2"),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=Sentinel2CloudMaskSpec(),
    )

    errors = validate_earth_engine_composite_request(request)
    assert errors == ()


def test_validate_earth_engine_composite_request_rejects_invalid_values() -> None:
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-1", " "),
        bands=("B2", "B2", ""),
        cloud_mask=Sentinel2CloudMaskSpec(),
    )

    errors = validate_earth_engine_composite_request(request)

    assert "scene_ids must not contain duplicates." in errors
    assert "scene_ids must not contain empty values." in errors
    assert "bands must not contain duplicates." in errors
    assert "bands must not contain empty values." in errors


def test_validate_earth_engine_export_request_accepts_valid_request() -> None:
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:padena"
        ),
        output_name="padena_sentinel2_stack",
        grid=make_exact_grid(),
    )

    errors = validate_earth_engine_export_request(request)
    assert errors == ()


def test_validate_earth_engine_export_request_rejects_invalid_request() -> None:
    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(image_id=" "),
        output_name=" ",
        grid=RasterGridSpec(
            crs="EPSG:32639",
            width=512,
            height=512,
            pixel_size_x=10.0,
            pixel_size_y=10.0,
        ),
    )

    errors = validate_earth_engine_export_request(request)
    assert "image.image_id must not be empty." in errors
    assert "output_name must not be empty." in errors
    assert (
        "grid.transform is required for exact raster export."
        in errors
    )

def test_validate_composite_request_includes_cloud_mask_errors() -> None:
    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1",),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=Sentinel2CloudMaskSpec(
            scl_band=" ",
            excluded_scl_classes=(),
        ),
    )

    errors = validate_earth_engine_composite_request(
        request
    )

    assert (
        "cloud_mask.scl_band must not be empty."
        in errors
    )
    assert (
        "cloud_mask.excluded_scl_classes must contain "
        "at least one class."
        in errors
    )