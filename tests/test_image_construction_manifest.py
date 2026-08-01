from geoai_dataset_curation.image_construction import (
    ImageConstructionResult,
    RasterGridSpec,
    image_construction_result_to_dict,
    build_raster_grid_id
)


def test_image_construction_result_to_dict_serializes_manifest() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )
    result = ImageConstructionResult(
        source_id="padena_aoi",
        output_name="padena_sentinel2_stack",
        scene_count=2,
        band_count=4,
        grid=grid,
        artifact_uri="artifacts/padena_sentinel2_stack.tif",
    )

    manifest = image_construction_result_to_dict(result)

    assert manifest == {
        "source_id": "padena_aoi",
        "output_name": "padena_sentinel2_stack",
        "scene_count": 2,
        "band_count": 4,
        "artifact_uri": "artifacts/padena_sentinel2_stack.tif",
        "has_artifact": True,
        "grid": {
            "grid_id": build_raster_grid_id(grid),
            "crs": "EPSG:32639",
            "width": 512,
            "height": 512,
            "pixel_size_x": 10.0,
            "pixel_size_y": 10.0,
            "transform": None,
        },
        
    }


def test_image_construction_result_to_dict_reports_missing_artifact() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )
    result = ImageConstructionResult(
        source_id="padena_aoi",
        output_name="padena_sentinel2_stack",
        scene_count=2,
        band_count=4,
        grid=grid,
        artifact_uri=" ",
    )

    manifest = image_construction_result_to_dict(result)

    assert manifest["has_artifact"] is False
    assert manifest["artifact_uri"] == " "
    assert manifest["grid"]["transform"] is None