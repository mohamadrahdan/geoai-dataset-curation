"Contracts for persistent real-image manifests"
from dataclasses import dataclass
from pathlib import Path
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)

REAL_IMAGE_MANIFEST_SCHEMA_VERSION = (
    "real-image-manifest-v1"
)


@dataclass(frozen=True)
class RealImageArtifactMetadata:
    """Persistent metadata snapshot for one real raster artifact."""

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
class RealImageManifest:
    "Manifest for one constructed real-image artifact."
    schema_version: str
    source_id: str
    output_name: str
    artifact_uri: str
    artifact: RealImageArtifactMetadata | None = None

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