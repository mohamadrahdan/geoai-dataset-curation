from geoai_dataset_curation.image_construction import (
    ImageConstructionRequest,
    RasterGridSpec,
    validate_image_construction_request,
)


def make_valid_request() -> ImageConstructionRequest:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=512,
        height=512,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
    )

    return ImageConstructionRequest(
        source_id="padena_aoi",
        scene_ids=("S2A_SCENE_001",),
        bands=("B2", "B3", "B4", "B8"),
        grid=grid,
        output_name="padena_sentinel2_stack",
    )


def test_validate_image_construction_request_accepts_valid_request() -> None:
    request = make_valid_request()
    errors = validate_image_construction_request(request)
    assert errors == ()


def test_validate_image_construction_request_rejects_empty_source_id() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=" ",
        scene_ids=request.scene_ids,
        bands=request.bands,
        grid=request.grid,
        output_name=request.output_name,
    )

    errors = validate_image_construction_request(invalid_request)
    assert "source_id must not be empty" in errors


def test_validate_image_construction_request_rejects_empty_scene_ids() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=request.source_id,
        scene_ids=(),
        bands=request.bands,
        grid=request.grid,
        output_name=request.output_name,
    )

    errors = validate_image_construction_request(invalid_request)
    assert "scene_ids must contain at least one scene" in errors


def test_validate_image_construction_request_rejects_duplicate_scene_ids() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=request.source_id,
        scene_ids=("S2A_SCENE_001", "S2A_SCENE_001"),
        bands=request.bands,
        grid=request.grid,
        output_name=request.output_name,
    )

    errors = validate_image_construction_request(invalid_request)
    assert "scene_ids must not contain duplicates" in errors


def test_validate_image_construction_request_rejects_invalid_bands() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=request.source_id,
        scene_ids=request.scene_ids,
        bands=("B2", "B2"),
        grid=request.grid,
        output_name=request.output_name,
    )

    errors = validate_image_construction_request(invalid_request)
    assert "bands must not contain duplicates" in errors


def test_validate_image_construction_request_rejects_empty_output_name() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=request.source_id,
        scene_ids=request.scene_ids,
        bands=request.bands,
        grid=request.grid,
        output_name=" ",
    )

    errors = validate_image_construction_request(invalid_request)
    assert "output_name must not be empty" in errors