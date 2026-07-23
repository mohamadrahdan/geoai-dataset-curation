"End-to-end vector validation pipeline"

from pathlib import Path
from geoai_dataset_curation.validation.contracts import ValidationSummary
from geoai_dataset_curation.validation.io import load_vector_file
from geoai_dataset_curation.validation.source import validate_source


def validate_vector_file(
    source_id: str,
    path: Path,
) -> ValidationSummary:
    "Load and validate one vector file"

    frame = load_vector_file(path)

    return validate_source(
        source_id=source_id,
        geometries=frame.geometry,
    )