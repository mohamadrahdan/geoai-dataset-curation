"Serialization helpers for image-construction results"

from typing import Any
from geoai_dataset_curation.image_construction.contracts import (ImageConstructionResult)
from geoai_dataset_curation.image_construction.grid_identity import (build_raster_grid_id)


def image_construction_result_to_dict(
    result: ImageConstructionResult,
) -> dict[str, Any]:
    "Convert an image-construction result into a serializable manifest"

    transform = result.grid.transform

    return {
        "source_id": result.source_id,
        "output_name": result.output_name,
        "scene_count": result.scene_count,
        "band_count": result.band_count,
        "artifact_uri": result.artifact_uri,
        "has_artifact": result.has_artifact,
        "grid": {
            "grid_id": build_raster_grid_id(result.grid),
            "crs": result.grid.crs,
            "width": result.grid.width,
            "height": result.grid.height,
            "pixel_size_x": result.grid.pixel_size_x,
            "pixel_size_y": result.grid.pixel_size_y,
            "transform": (
                {
                    "a": transform.a,
                    "b": transform.b,
                    "c": transform.c,
                    "d": transform.d,
                    "e": transform.e,
                    "f": transform.f,
                    "coefficients": list(transform.as_tuple),
                }
                if transform is not None
                else None
            ),
        },
    }