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