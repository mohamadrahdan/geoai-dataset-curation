"Source-registry contracts for private geospatial inputs"

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SourceRecord:
    "Metadata required to register one geospatial source"

    id: str
    category: str
    geometry_type: str
    access: str
    role: str
    status: str
    path: Optional[str] = None
    format: Optional[str] = None
    crs: Optional[str] = None
    label_value: Optional[int] = None