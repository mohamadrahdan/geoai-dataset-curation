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


class VisualReviewStatus(StrEnum):
    "Human visual-review decision for one pair"
    PENDING = "pending"
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


@dataclass(frozen=True)
class PairVisualReview:
    "Human visual-review decision for one image-mask pair"
    pair_id: str
    tile_id: str
    status: VisualReviewStatus
    notes: str = ""


VISUAL_REVIEW_CATALOG_SCHEMA_VERSION = (
    "pair-visual-review-catalog-v1"
)


@dataclass(frozen=True)
class VisualReviewCatalog:
    "Human visual-review decisions for one pair catalog"
    schema_version: str
    output_name: str
    pair_catalog_id: str
    reviewer: str
    reviews: tuple[PairVisualReview, ...]

    @property
    def review_count(self) -> int:
        return len(self.reviews)

    @property
    def pending_count(self) -> int:
        return sum(
            review.status == VisualReviewStatus.PENDING
            for review in self.reviews
        )

    @property
    def pass_count(self) -> int:
        return sum(
            review.status == VisualReviewStatus.PASS
            for review in self.reviews
        )

    @property
    def review_required_count(self) -> int:
        return sum(
            review.status == VisualReviewStatus.REVIEW
            for review in self.reviews
        )

    @property
    def fail_count(self) -> int:
        return sum(
            review.status == VisualReviewStatus.FAIL
            for review in self.reviews
        )

    @property
    def is_complete(self) -> bool:
        return bool(self.reviews) and self.pending_count == 0

    @property
    def status(self) -> QCStatus:
        if self.fail_count:
            return QCStatus.FAIL

        if (
            not self.reviews
            or self.pending_count
            or self.review_required_count
        ):
            return QCStatus.WARNING

        return QCStatus.PASS


PAIR_QC_REPORT_SCHEMA_VERSION = "pair-quality-control-report-v1"


@dataclass(frozen=True)
class PairImageStatistics:
    "Per-band image statistics linked to one pair"
    pair_id: str
    tile_id: str
    bands: tuple[ImageBandStatistics, ...]


@dataclass(frozen=True)
class PairQCReport:
    "Automated quality-control report for one pair catalog"
    schema_version: str
    pair_catalog_id: str
    traceability: TraceabilityQCResult
    pair_results: tuple[PairQCResult, ...]
    image_statistics: tuple[PairImageStatistics, ...]

    @property
    def pair_count(self) -> int:
        return len(self.pair_results)

    @property
    def pass_count(self) -> int:
        return sum(result.status == QCStatus.PASS for result in self.pair_results)

    @property
    def warning_count(self) -> int:
        return sum(result.status == QCStatus.WARNING for result in self.pair_results)

    @property
    def fail_count(self) -> int:
        return sum(result.status == QCStatus.FAIL for result in self.pair_results)

    @property
    def finding_count(self) -> int:
        return sum(len(result.findings) for result in self.pair_results) + len(self.traceability.findings)

    @property
    def status(self) -> QCStatus:
        if self.traceability.status == QCStatus.FAIL or self.fail_count:
            return QCStatus.FAIL

        if self.traceability.status == QCStatus.WARNING or self.warning_count:
            return QCStatus.WARNING

        return QCStatus.PASS