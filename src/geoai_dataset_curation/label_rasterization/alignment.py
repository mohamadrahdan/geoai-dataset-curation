"Direct alignment verification between image and label raster artifacts"
from dataclasses import dataclass
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)


@dataclass(frozen=True)
class RasterPairAlignmentResult:
    "Result of comparing the spatial structure of two physical rasters"
    crs_matches: bool
    width_matches: bool
    height_matches: bool
    transform_matches: bool

    @property
    def matches(self) -> bool:
        "Return whether both rasters are exactly pixel-aligned"
        return (
            self.crs_matches
            and self.width_matches
            and self.height_matches
            and self.transform_matches
        )


def verify_raster_pair_alignment(
    *,
    image: RasterArtifactMetadata,
    label: RasterArtifactMetadata,
) -> RasterPairAlignmentResult:
    "Compare image and label raster metadata directly"
    return RasterPairAlignmentResult(
        crs_matches=image.crs == label.crs,
        width_matches=image.width == label.width,
        height_matches=image.height == label.height,
        transform_matches=image.transform == label.transform,
    )