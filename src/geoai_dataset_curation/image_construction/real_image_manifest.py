"Contracts for persistent real-image manifests"
from dataclasses import dataclass
from pathlib import Path
from datetime import date
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    ScenePreparationResult,
)
from geoai_dataset_curation.image_construction.contracts import (
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.image_construction.validation import (
    validate_exact_raster_grid_spec,
)

REAL_IMAGE_MANIFEST_SCHEMA_VERSION = (
    "real-image-manifest-v1"
)


@dataclass(frozen=True)
class RealImageArtifactMetadata:
    "Persistent metadata snapshot for one real raster artifact"
    file_size_bytes: int
    driver: str
    width: int
    height: int
    band_count: int
    dtypes: tuple[str, ...]


def create_real_image_artifact_metadata(
    metadata: RasterArtifactMetadata,
) -> RealImageArtifactMetadata:
    "Create persistent artifact metadata from an inspected raster"
    file_size_bytes = metadata.path.stat().st_size
    if file_size_bytes <= 0:
        raise ValueError(
            "Raster artifact must not be empty."
        )
    return RealImageArtifactMetadata(
        file_size_bytes=file_size_bytes,
        driver=metadata.driver,
        width=metadata.width,
        height=metadata.height,
        band_count=metadata.band_count,
        dtypes=metadata.dtypes,
    )


@dataclass(frozen=True)
class RealImageSceneProvenance:
    "Traceable metadata for one Sentinel-2 source scene"
    scene_id: str
    acquisition_date: date
    cloud_cover: float
    collection: str


@dataclass(frozen=True)
class RealImageCompositeProvenance:
    "Processing provenance for one Sentinel-2 composite"
    scenes: tuple[RealImageSceneProvenance, ...]
    bands: tuple[str, ...]
    aggregation_method: str
    cloud_mask_band: str
    excluded_cloud_mask_classes: tuple[int, ...]


@dataclass(frozen=True)
class RealImageGridMetadata:
    "Persistent snapshot of one approved exact raster grid"
    grid_id: str
    crs: str
    width: int
    height: int
    pixel_size_x: float
    pixel_size_y: float
    transform: tuple[
        float,
        float,
        float,
        float,
        float,
        float,
    ]


@dataclass(frozen=True)
class RealImageManifest:
    "Manifest for one constructed real-image artifact."
    schema_version: str
    source_id: str
    output_name: str
    artifact_uri: str
    artifact: RealImageArtifactMetadata | None = None
    provenance: RealImageCompositeProvenance | None = None
    grid: RealImageGridMetadata | None = None

    @property
    def has_artifact(self) -> bool:
        "Return whether the manifest references an artifact"
        return bool(
            self.artifact_uri.strip()
        )
    

def create_real_image_manifest(
    *,
    source_id: str,
    output_name: str,
    artifact_uri: str,
) -> RealImageManifest:
    "Create the base manifest for one real-image artifact"
    if not source_id.strip():
        raise ValueError("source_id must not be empty.")

    if not output_name.strip():
        raise ValueError("output_name must not be empty.")

    if not artifact_uri.strip():
        raise ValueError("artifact_uri must not be empty.")

    return RealImageManifest(
        schema_version=(
            REAL_IMAGE_MANIFEST_SCHEMA_VERSION
        ),
        source_id=source_id,
        output_name=output_name,
        artifact_uri=artifact_uri,
    )


def create_real_image_composite_provenance(
    *,
    scene_preparation: ScenePreparationResult,
    composite_request: EarthEngineCompositeRequest,
) -> RealImageCompositeProvenance:
    "Create persistent provenance for one real Sentinel-2 composite"
    selected_scene_ids = tuple(
        scene.scene_id
        for scene in scene_preparation.selected_scenes
    )

    if selected_scene_ids != composite_request.scene_ids:
        raise ValueError(
            "Composite scene_ids must exactly match "
            "the prepared selected scenes."
        )

    scenes = tuple(
        RealImageSceneProvenance(
            scene_id=scene.scene_id,
            acquisition_date=scene.acquisition_date,
            cloud_cover=scene.cloud_cover,
            collection=scene.collection,
        )
        for scene in scene_preparation.selected_scenes
    )

    return RealImageCompositeProvenance(
        scenes=scenes,
        bands=composite_request.bands,
        aggregation_method=(
            composite_request.aggregation_method.value
        ),
        cloud_mask_band=(
            composite_request.cloud_mask.scl_band
        ),
        excluded_cloud_mask_classes=(
            composite_request
            .cloud_mask
            .excluded_scl_classes
        ),
    )


def create_real_image_grid_metadata(
    grid: RasterGridSpec,
) -> RealImageGridMetadata:
    "Create persistent metadata from one approved exact raster grid"
    errors = validate_exact_raster_grid_spec(
        grid
    )
    if errors:
        raise ValueError(
            "Cannot create real-image grid metadata: "
            + "; ".join(errors)
        )
    transform = grid.transform
    if transform is None:
        raise ValueError(
            "Exact raster grid requires an affine transform."
        )
    return RealImageGridMetadata(
        grid_id=build_raster_grid_id(grid),
        crs=grid.crs,
        width=grid.width,
        height=grid.height,
        pixel_size_x=grid.pixel_size_x,
        pixel_size_y=grid.pixel_size_y,
        transform=transform.as_tuple,
    )