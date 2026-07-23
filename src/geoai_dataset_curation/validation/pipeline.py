"End-to-end vector validation pipeline"

from pathlib import Path
from geoai_dataset_curation.validation.contracts import ValidationSummary
from geoai_dataset_curation.validation.io import load_vector_file
from geoai_dataset_curation.validation.metadata import (validate_source_metadata)
from geoai_dataset_curation.validation.source import validate_source


def validate_vector_file(
    source_id: str,
    path: Path,
) -> ValidationSummary:
    "Load and validate one vector file"
    frame = load_vector_file(path)
    geometry_summary = validate_source(
        source_id=source_id,
        geometries=frame.geometry,
    )
    metadata_issues = validate_source_metadata(frame)

    return ValidationSummary(
        source_id=geometry_summary.source_id,
        feature_count=geometry_summary.feature_count,
        valid_feature_count=geometry_summary.valid_feature_count,
        invalid_feature_count=geometry_summary.invalid_feature_count,
        issues=geometry_summary.issues + metadata_issues,
    )