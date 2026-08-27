"Verification of raster artifacts against approved grid contracts"
from __future__ import annotations
from dataclasses import dataclass
from affine import Affine
from geoai_dataset_curation.image_construction.contracts import (RasterGridSpec)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)


@dataclass(frozen=True)
class RasterGridVerificationResult:
    "Result of comparing one raster artifact to an approved grid"
    crs_matches: bool
    width_matches: bool
    height_matches: bool
    transform_matches: bool

    @property
    def matches(self) -> bool:
        "Return whether all exact-grid checks passed"
        return (
            self.crs_matches
            and self.width_matches
            and self.height_matches
            and self.transform_matches
        )


def verify_raster_against_grid(
    metadata: RasterArtifactMetadata,
    grid: RasterGridSpec,
) -> RasterGridVerificationResult:
    "Compare raster metadata against one approved raster grid"
    if grid.transform is None:
        raise ValueError("Approved raster grid requires an affine transform.")
    expected_transform = Affine(*grid.transform.as_tuple)
    return RasterGridVerificationResult(
        crs_matches=(
            metadata.crs == grid.crs
        ),
        width_matches=(
            metadata.width == grid.width
        ),
        height_matches=(
            metadata.height == grid.height
        ),
        transform_matches=(
            metadata.transform == expected_transform
        ),
    )