"Validation result contracts for geospatial vector sources"

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    "One validation problem found in a source dataset"

    code: str
    message: str
    feature_index: int | None = None


@dataclass(frozen=True)
class ValidationSummary:
    "Summary of one vector-source validation run"

    source_id: str
    feature_count: int
    valid_feature_count: int
    invalid_feature_count: int
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        "Return whether the source contains no invalid features"

        return self.invalid_feature_count == 0