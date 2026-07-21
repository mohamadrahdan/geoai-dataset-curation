from geoai_dataset_curation.validation import (
    ValidationIssue,
    ValidationSummary,
)


def test_validation_summary_is_valid_without_invalid_features() -> None:
    summary = ValidationSummary(
        source_id="padena_landslides",
        feature_count=3,
        valid_feature_count=3,
        invalid_feature_count=0,
    )

    assert summary.is_valid is True


def test_validation_summary_is_invalid_with_issues() -> None:
    issue = ValidationIssue(
        code="invalid_geometry",
        message="Geometry is invalid.",
        feature_index=2,
    )

    summary = ValidationSummary(
        source_id="padena_landslides",
        feature_count=3,
        valid_feature_count=2,
        invalid_feature_count=1,
        issues=(issue,),
    )

    assert summary.is_valid is False
    assert summary.issues[0].code == "invalid_geometry"