"Load source-registry metadata from YAML"

from pathlib import Path
from typing import Any

import yaml

from geoai_dataset_curation.contracts.source_registry import SourceRecord


def load_source_registry(path: Path) -> list[SourceRecord]:
    "Load and convert source-registry entries into SourceRecord objects"

    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file)

    return [SourceRecord(**item) for item in data["sources"]]