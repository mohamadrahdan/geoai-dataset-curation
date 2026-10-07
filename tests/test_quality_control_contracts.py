from geoai_dataset_curation.quality_control import (
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
    QCStatus,
    validate_pair_qc_result,
    validate_qc_finding,
)


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)


def test_pair_qc_result_passes_without_findings() -> None:
    result = PairQCResult(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
    )
    assert result.status == QCStatus.PASS
    assert result.has_blocking_findings is False


def test_warning_finding_is_non_blocking() -> None:
    result = PairQCResult(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        findings=(
            QCFinding(
                code="image.low_variance",
                severity=QCFindingSeverity.WARNING,
                message="One image band has low variance.",
            ),
        ),
    )
    assert result.status == QCStatus.WARNING
    assert result.has_blocking_findings is False


def test_error_finding_blocks_the_pair() -> None:
    result = PairQCResult(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        findings=(
            QCFinding(
                code="mask.invalid_value",
                severity=QCFindingSeverity.ERROR,
                message="The mask contains an invalid value.",
            ),
            QCFinding(
                code="image.low_variance",
                severity=QCFindingSeverity.WARNING,
                message="One image band has low variance.",
            ),
        ),
    )
    assert result.status == QCStatus.FAIL
    assert result.has_blocking_findings is True


def test_valid_qc_finding_has_no_contract_errors() -> None:
    finding = QCFinding(
        code="mask.invalid_value",
        severity=QCFindingSeverity.ERROR,
        message="The mask contains an invalid value.",
    )
    assert validate_qc_finding(finding) == ()


def test_invalid_qc_finding_reports_all_errors() -> None:
    finding = QCFinding(
        code="Mask Invalid Value",
        severity="error",  # type: ignore[arg-type]
        message=" ",
    )
    assert validate_qc_finding(finding) == (
        "code must be a lowercase machine-readable identifier.",
        "severity must be a QCFindingSeverity.",
        "message must not be empty.",
    )


def test_valid_pair_qc_result_has_no_contract_errors() -> None:
    result = PairQCResult(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        findings=(
            QCFinding(
                code="image.non_finite_value",
                severity=QCFindingSeverity.ERROR,
                message="The image contains a non-finite value.",
            ),
        ),
    )
    assert validate_pair_qc_result(result) == ()


def test_invalid_pair_qc_result_reports_context_errors() -> None:
    result = PairQCResult(
        pair_id="not-a-pair-id",
        tile_id="not-a-tile-id",
        findings=[],  # type: ignore[arg-type]
    )

    assert validate_pair_qc_result(result) == (
        "pair_id must be a valid SHA-256 identity.",
        "tile_id must be a valid SHA-256 identity.",
        "findings must be a tuple.",
    )