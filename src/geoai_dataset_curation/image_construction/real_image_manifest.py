"Contracts for persistent real-image manifests"
from dataclasses import dataclass
from pathlib import Path
from datetime import date
from typing import Any
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
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RetrievedRasterArtifact,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
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
class RealImageExportTrace:
    "Traceability metadata for one exported and retrieved raster artifact."
    task_id: str
    destination: str
    destination_folder: str
    remote_artifact_uri: str
    local_path: Path


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
    export_trace: RealImageExportTrace | None = None

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


def create_real_image_export_trace(
    *,
    export_request: EarthEngineExportRequest,
    export_task: EarthEngineExportTaskReference,
    retrieved_artifact: RetrievedRasterArtifact,
) -> RealImageExportTrace:
    "Create traceability metadata for one export and retrieval path"
    if not export_task.task_id.strip():
        raise ValueError("export task_id must not be empty.")
    if not retrieved_artifact.source.uri.strip():
        raise ValueError("remote artifact URI must not be empty.")

    return RealImageExportTrace(
        task_id=export_task.task_id,
        destination=export_request.destination.value,
        destination_folder=(export_request.destination_folder),
        remote_artifact_uri=(retrieved_artifact.source.uri),
        local_path=(retrieved_artifact.local_path),
    )


def validate_real_image_manifest(
    manifest: RealImageManifest,
) -> tuple[str, ...]:
    "Return consistency errors for one complete real-image manifest"
    errors: list[str] = []

    if (
        manifest.schema_version
        != REAL_IMAGE_MANIFEST_SCHEMA_VERSION
    ):
        errors.append("schema_version is not supported.")

    if not manifest.source_id.strip():
        errors.append("source_id must not be empty.")

    if not manifest.output_name.strip():
        errors.append("output_name must not be empty.")

    if not manifest.artifact_uri.strip():
        errors.append("artifact_uri must not be empty.")

    if manifest.artifact is None:
        errors.append("artifact metadata is required.")

    if manifest.provenance is None:
        errors.append(
            "composite provenance is required."
        )

    if manifest.grid is None:
        errors.append("grid metadata is required.")

    if manifest.export_trace is None:
        errors.append("export trace is required.")

    if (
        manifest.export_trace is not None
        and manifest.artifact_uri
        != manifest.export_trace.remote_artifact_uri
    ):
        errors.append(
            "artifact_uri must match "
            "export_trace.remote_artifact_uri."
        )

    if (
        manifest.artifact is not None
        and manifest.grid is not None
    ):
        if (
            manifest.artifact.width
            != manifest.grid.width
        ):
            errors.append(
                "artifact width must match grid width."
            )

        if (
            manifest.artifact.height
            != manifest.grid.height
        ):
            errors.append(
                "artifact height must match grid height."
            )

    if (
        manifest.artifact is not None
        and manifest.provenance is not None
        and manifest.artifact.band_count
        != len(manifest.provenance.bands)
    ):
        errors.append(
            "artifact band_count must match "
            "the composite band count."
        )
    return tuple(errors)


def real_image_manifest_to_dict(
    manifest: RealImageManifest,
) -> dict[str, Any]:
    "Serialize one complete real-image manifest"
    errors = validate_real_image_manifest(
        manifest
    )

    if errors:
        raise ValueError(
            "Cannot serialize invalid real-image manifest: "
            + "; ".join(errors)
        )
    artifact = manifest.artifact
    provenance = manifest.provenance
    grid = manifest.grid
    export_trace = manifest.export_trace

    if (
        artifact is None
        or provenance is None
        or grid is None
        or export_trace is None
    ):
        raise RuntimeError("Validated real-image manifest is incomplete.")

    return {
        "schema_version": manifest.schema_version,
        "source_id": manifest.source_id,
        "output_name": manifest.output_name,
        "artifact_uri": manifest.artifact_uri,
        "artifact": {
            "file_size_bytes": (
                artifact.file_size_bytes
            ),
            "driver": artifact.driver,
            "width": artifact.width,
            "height": artifact.height,
            "band_count": artifact.band_count,
            "dtypes": list(
                artifact.dtypes
            ),
        },
        "provenance": {
            "scenes": [
                {
                    "scene_id": scene.scene_id,
                    "acquisition_date": (
                        scene.acquisition_date.isoformat()
                    ),
                    "cloud_cover": scene.cloud_cover,
                    "collection": scene.collection,
                }
                for scene in provenance.scenes
            ],
            "bands": list(provenance.bands),
            "aggregation_method": (provenance.aggregation_method),
            "cloud_mask_band": (provenance.cloud_mask_band),
            "excluded_cloud_mask_classes": list(provenance.excluded_cloud_mask_classes),
        },
        "grid": {
            "grid_id": grid.grid_id,
            "crs": grid.crs,
            "width": grid.width,
            "height": grid.height,
            "pixel_size_x": grid.pixel_size_x,
            "pixel_size_y": grid.pixel_size_y,
            "transform": list(
                grid.transform
            ),
        },
        "export_trace": {
            "task_id": export_trace.task_id,
            "destination": (export_trace.destination),
            "destination_folder": (export_trace.destination_folder),
            "remote_artifact_uri": (export_trace.remote_artifact_uri),
            "local_path": str(export_trace.local_path),
        },
    }


def create_complete_real_image_manifest(
    *,
    scene_preparation: ScenePreparationResult,
    composite_request: EarthEngineCompositeRequest,
    export_request: EarthEngineExportRequest,
    export_task: EarthEngineExportTaskReference,
    retrieved_artifact: RetrievedRasterArtifact,
    inspected_metadata: RasterArtifactMetadata,
    approved_grid: RasterGridSpec,
) -> RealImageManifest:
    "Assemble one complete validated real-image manifest"
    if (scene_preparation.source_id.strip() == ""):
        raise ValueError("scene preparation source_id must not be empty.")

    if (export_request.image.image_id.strip() == ""):
        raise ValueError("export image reference must not be empty.")

    if (retrieved_artifact.local_path != inspected_metadata.path):
        raise ValueError(
            "Inspected raster path must match "
            "the retrieved artifact path."
        )

    artifact = create_real_image_artifact_metadata(inspected_metadata)

    provenance = create_real_image_composite_provenance(
        scene_preparation=scene_preparation,
        composite_request=composite_request,
    )

    grid = create_real_image_grid_metadata(approved_grid)

    export_trace = create_real_image_export_trace(
        export_request=export_request,
        export_task=export_task,
        retrieved_artifact=retrieved_artifact,
    )

    manifest = RealImageManifest(
        schema_version=(
            REAL_IMAGE_MANIFEST_SCHEMA_VERSION
        ),
        source_id=scene_preparation.source_id,
        output_name=export_request.output_name,
        artifact_uri=(
            retrieved_artifact.source.uri
        ),
        artifact=artifact,
        provenance=provenance,
        grid=grid,
        export_trace=export_trace,
    )
    errors = validate_real_image_manifest(
        manifest
    )
    if errors:
        raise ValueError(
            "Cannot assemble real-image manifest: "
            + "; ".join(errors)
        )

    return manifest