from geoai_dataset_curation.validation import (
    ValidationIssue,
    ValidationSummary,
    validation_summary_to_dict,
)


def test_validation_summary_is_serialized() -> None:
    summary = ValidationSummary(
        source_id="padena_landslides",
        feature_count=3,
        valid_feature_count=2,
        invalid_feature_count=1,
        issues=(
            ValidationIssue(
                code="invalid_geometry",
                message="Self-intersection.",
                feature_index=2,
            ),
        ),
    )

    result = validation_summary_to_dict(summary)
    assert result == {
        "source_id": "padena_landslides",
        "feature_count": 3,
        "valid_feature_count": 2,
        "invalid_feature_count": 1,
        "is_valid": False,
        "issues": [
            {
                "code": "invalid_geometry",
                "message": "Self-intersection.",
                "feature_index": 2,
            }
        ],
    }


def test_valid_summary_serializes_without_issues() -> None:
    summary = ValidationSummary(
        source_id="padena_aoi",
        feature_count=1,
        valid_feature_count=1,
        invalid_feature_count=0,
    )

    result = validation_summary_to_dict(summary)
    assert result["is_valid"] is True
    assert result["issues"] == []