from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    ImageConstructionResult,
    RasterGridSpec,
    image_construction_result_to_dict,
)


def test_image_manifest_serializes_exact_affine_transform() -> None:
    transform = AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=500000.0,
        d=0.0,
        e=-10.0,
        f=3600000.0,
    )
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=transform,
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

    assert manifest["grid"]["transform"] == {
        "a": 10.0,
        "b": 0.0,
        "c": 500000.0,
        "d": 0.0,
        "e": -10.0,
        "f": 3600000.0,
        "coefficients": [
            10.0,
            0.0,
            500000.0,
            0.0,
            -10.0,
            3600000.0,
        ],
    }


def test_image_manifest_serializes_missing_transform_as_none() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )
    result = ImageConstructionResult(
        source_id="padena_aoi",
        output_name="legacy_stack",
        scene_count=1,
        band_count=4,
        grid=grid,
        artifact_uri="artifacts/legacy_stack.tif",
    )

    manifest = image_construction_result_to_dict(result)

    assert manifest["grid"]["transform"] is None