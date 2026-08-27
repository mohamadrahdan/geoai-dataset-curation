"Contracts for retrieving exported raster artifacts"
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class RasterArtifactFormat(StrEnum):
    "Supported raster artifact formats"
    GEOTIFF = "geotiff"


@dataclass(frozen=True)
class RemoteRasterArtifact:
    "Reference to one remotely stored raster artifact"
    uri: str
    format: RasterArtifactFormat


@dataclass(frozen=True)
class RasterArtifactRetrievalRequest:
    "Request for retrieving one remote raster artifact"
    artifact: RemoteRasterArtifact
    local_path: Path


@dataclass(frozen=True)
class RetrievedRasterArtifact:
    "Reference to one raster artifact retrieved to local storage"
    source: RemoteRasterArtifact
    local_path: Path

    @property
    def exists(self) -> bool:
        "Return whether the retrieved artifact exists locally"
        return self.local_path.is_file()