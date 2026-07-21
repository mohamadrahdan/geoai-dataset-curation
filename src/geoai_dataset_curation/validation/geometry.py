"Geometry-level validation checks"

from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity
from geoai_dataset_curation.validation.contracts import ValidationIssue


def validate_geometry(
    geometry: BaseGeometry | None,
    feature_index: int | None = None,
) -> tuple[ValidationIssue, ...]:
    "Validate one geometry and return all detected issues"

    issues: list[ValidationIssue] = []

    if geometry is None:
        issues.append(
            ValidationIssue(
                code="missing_geometry",
                message="Geometry is missing.",
                feature_index=feature_index,
            )
        )
        return tuple(issues)

    if geometry.is_empty:
        issues.append(
            ValidationIssue(
                code="empty_geometry",
                message="Geometry is empty.",
                feature_index=feature_index,
            )
        )

    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        issues.append(
            ValidationIssue(
                code="unsupported_geometry_type",
                message=f"Unsupported geometry type: {geometry.geom_type}.",
                feature_index=feature_index,
            )
        )

    if not geometry.is_valid:
        issues.append(
            ValidationIssue(
                code="invalid_geometry",
                message=explain_validity(geometry),
                feature_index=feature_index,
            )
        )

    return tuple(issues)