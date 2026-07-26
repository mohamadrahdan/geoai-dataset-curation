import pytest
from geoai_dataset_curation.image_construction import (
    ImageConstructionRequest,
    RasterGridSpec,
    construct_image,
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
        scene_ids=("S2A_SCENE_001", "S2B_SCENE_002"),
        bands=("B2", "B3", "B4", "B8"),
        grid=grid,
        output_name="padena_sentinel2_stack",
    )


def test_construct_image_returns_structured_result() -> None:
    request = make_valid_request()

    result = construct_image(
        request=request,
        artifact_uri="artifacts/padena_sentinel2_stack.tif",
    )

    assert result.source_id == "padena_aoi"
    assert result.output_name == "padena_sentinel2_stack"
    assert result.scene_count == 2
    assert result.band_count == 4
    assert result.grid == request.grid
    assert result.artifact_uri == "artifacts/padena_sentinel2_stack.tif"
    assert result.has_artifact is True


def test_construct_image_rejects_invalid_request() -> None:
    request = make_valid_request()
    invalid_request = ImageConstructionRequest(
        source_id=" ",
        scene_ids=request.scene_ids,
        bands=request.bands,
        grid=request.grid,
        output_name=request.output_name,
    )

    with pytest.raises(ValueError) as error:
        construct_image(
            request=invalid_request,
            artifact_uri="artifacts/padena_sentinel2_stack.tif",
        )

    assert "source_id must not be empty" in str(error.value)


def test_construct_image_rejects_empty_artifact_uri() -> None:
    request = make_valid_request()

    with pytest.raises(ValueError) as error:
        construct_image(
            request=request,
            artifact_uri=" ",
        )

    assert "artifact_uri must not be empty." in str(error.value)