"Validation of complete vector sources"

from collections.abc import Iterable
from shapely.geometry.base import BaseGeometry
from geoai_dataset_curation.validation.contracts import ValidationSummary
from geoai_dataset_curation.validation.geometry import validate_geometry


def validate_source(
    source_id: str,
    geometries: Iterable[BaseGeometry | None],
) -> ValidationSummary:
    "Validate all geometries from one registered vector source"
    
    geometry_list = list(geometries)
    issues = tuple(
        issue
        for feature_index, geometry in enumerate(geometry_list)
        for issue in validate_geometry(
            geometry,
            feature_index=feature_index,
        )
    )

    invalid_indexes = {
        issue.feature_index
        for issue in issues
        if issue.feature_index is not None
    }

    invalid_feature_count = len(invalid_indexes)
    feature_count = len(geometry_list)

    return ValidationSummary(
        source_id=source_id,
        feature_count=feature_count,
        valid_feature_count=feature_count - invalid_feature_count,
        invalid_feature_count=invalid_feature_count,
        issues=issues,
    )