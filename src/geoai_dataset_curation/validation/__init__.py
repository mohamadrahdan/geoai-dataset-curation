"Vector-validation components"

from geoai_dataset_curation.validation.contracts import (ValidationIssue, ValidationSummary)
from geoai_dataset_curation.validation.geometry import validate_geometry
from geoai_dataset_curation.validation.io import load_vector_file
from geoai_dataset_curation.validation.report import (validation_summary_to_dict)
from geoai_dataset_curation.validation.source import validate_source
from geoai_dataset_curation.validation.pipeline import validate_vector_file

__all__ = [
    "ValidationIssue",
    "ValidationSummary",
    "validate_geometry",
    "validate_source",
    "validation_summary_to_dict",
    "load_vector_file",
    "validate_vector_file",
]