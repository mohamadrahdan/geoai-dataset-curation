"Contracts for image-mask pair quality control"
from dataclasses import dataclass, field
from enum import StrEnum


class QCFindingSeverity(StrEnum):
    "Severity of one quality-control finding"
    WARNING = "warning"
    ERROR = "error"


class QCStatus(StrEnum):
    "Overall outcome of one quality-control result"
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True)
class QCFinding:
    "One machine-readable quality-control finding"
    code: str
    severity: QCFindingSeverity
    message: str


@dataclass(frozen=True)
class PairQCResult:
    "Quality-control result for one image-mask pair"
    pair_id: str
    tile_id: str
    findings: tuple[QCFinding, ...] = field(
        default_factory=tuple
    )

    @property
    def status(self) -> QCStatus:
        "Derive the overall result from finding severities"
        if any(
            finding.severity == QCFindingSeverity.ERROR
            for finding in self.findings
        ):
            return QCStatus.FAIL

        if any(
            finding.severity == QCFindingSeverity.WARNING
            for finding in self.findings
        ):
            return QCStatus.WARNING

        return QCStatus.PASS

    @property
    def has_blocking_findings(self) -> bool:
        "Return whether the pair must be blocked"
        return self.status == QCStatus.FAIL


@dataclass(frozen=True)
class ImageBandStatistics:
    "Descriptive statistics for one image band"
    band_index: int
    pixel_count: int
    finite_pixel_count: int
    non_finite_pixel_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    standard_deviation: float | None

    @property
    def is_constant(self) -> bool:
        "Return whether all finite values are identical"
        return (
            self.finite_pixel_count > 0
            and self.minimum == self.maximum
        )


@dataclass(frozen=True)
class ImageContentInspection:
    "Image-content QC result and its per-band statistics"
    pair_result: PairQCResult
    band_statistics: tuple[ImageBandStatistics, ...]

    @property
    def status(self) -> QCStatus:
        "Return the derived pair QC status"
        return self.pair_result.status


@dataclass(frozen=True)
class TraceabilityQCResult:
    "Cross-artifact traceability result for one pair catalog"
    pair_catalog_id: str
    expected_pair_count: int
    verified_pair_count: int
    discovered_image_file_count: int
    discovered_mask_file_count: int
    findings: tuple[QCFinding, ...] = field(
        default_factory=tuple
    )

    @property
    def status(self) -> QCStatus:
        "Derive the traceability status from its findings"
        if any(
            finding.severity == QCFindingSeverity.ERROR
            for finding in self.findings
        ):
            return QCStatus.FAIL
        if any(
            finding.severity == QCFindingSeverity.WARNING
            for finding in self.findings
        ):
            return QCStatus.WARNING
        return QCStatus.PASS

    @property
    def has_blocking_findings(self) -> bool:
        "Return whether traceability verification failed"
        return self.status == QCStatus.FAIL