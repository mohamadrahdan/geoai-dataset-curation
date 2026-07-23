"Source-level metadata validation checks"

import geopandas as gpd
from geoai_dataset_curation.validation.contracts import ValidationIssue


def validate_source_metadata(
    frame: gpd.GeoDataFrame,
) -> tuple[ValidationIssue, ...]:
    "Validate metadata and structure of one vector source"

    issues: list[ValidationIssue] = []
    if frame.empty:
        issues.append(
            ValidationIssue(
                code="empty_source",
                message="Vector source contains no features.",
            )
        )

    if frame.crs is None:
        issues.append(
            ValidationIssue(
                code="missing_crs",
                message="Vector source has no coordinate reference system.",
            )
        )

    return tuple(issues)