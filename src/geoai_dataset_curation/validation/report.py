"Serialization helpers for vector-validation summaries"

from typing import Any
from geoai_dataset_curation.validation.contracts import ValidationSummary


def validation_summary_to_dict(
    summary: ValidationSummary,
) -> dict[str, Any]:
    "Convert one validation summary into a serializable dictionary"

    return {
        "source_id": summary.source_id,
        "feature_count": summary.feature_count,
        "valid_feature_count": summary.valid_feature_count,
        "invalid_feature_count": summary.invalid_feature_count,
        "is_valid": summary.is_valid,
        "issues": [
            {
                "code": issue.code,
                "message": issue.message,
                "feature_index": issue.feature_index,
            }
            for issue in summary.issues
        ],
    }