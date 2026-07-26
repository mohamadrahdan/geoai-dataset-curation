"End-to-end raster image-construction pipeline"

from geoai_dataset_curation.image_construction.contracts import (
    ImageConstructionRequest,
    ImageConstructionResult,
)
from geoai_dataset_curation.image_construction.validation import (
    validate_image_construction_request,
)


def construct_image(
    request: ImageConstructionRequest,
    artifact_uri: str,
) -> ImageConstructionResult:
    "Validate a request and return a structured construction result"

    errors = validate_image_construction_request(request)

    if errors:
        raise ValueError("; ".join(errors))

    if not artifact_uri.strip():
        raise ValueError("artifact_uri must not be empty.")

    return ImageConstructionResult(
        source_id=request.source_id,
        output_name=request.output_name,
        scene_count=len(request.scene_ids),
        band_count=len(request.bands),
        grid=request.grid,
        artifact_uri=artifact_uri,
    )