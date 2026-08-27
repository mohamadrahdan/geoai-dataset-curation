"Contracts for persistent real-image manifests"
from dataclasses import dataclass


REAL_IMAGE_MANIFEST_SCHEMA_VERSION = (
    "real-image-manifest-v1"
)


@dataclass(frozen=True)
class RealImageManifest:
    "Identity envelope for one constructed real-image artifact"
    schema_version: str
    source_id: str
    output_name: str
    artifact_uri: str

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