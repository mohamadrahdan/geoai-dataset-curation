"Pixel-grid alignment checks for raster artifacts"
from __future__ import annotations
from dataclasses import dataclass
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)


@dataclass(frozen=True)
class RasterAlignmentResult:
    "Result of comparing two raster pixel grids"
    crs_matches: bool
    width_matches: bool
    height_matches: bool
    transform_matches: bool

    @property
    def aligned(self) -> bool:
        "Return whether both rasters share the exact pixel grid"
        return (
            self.crs_matches
            and self.width_matches
            and self.height_matches
            and self.transform_matches
        )


def verify_raster_alignment(
    reference: RasterArtifactMetadata,
    candidate: RasterArtifactMetadata,
) -> RasterAlignmentResult:
    "Verify exact pixel-grid alignment between two rasters"
    return RasterAlignmentResult(
        crs_matches=(reference.crs == candidate.crs),
        width_matches=(reference.width == candidate.width),
        height_matches=(reference.height == candidate.height),
        transform_matches=(reference.transform == candidate.transform),
    )