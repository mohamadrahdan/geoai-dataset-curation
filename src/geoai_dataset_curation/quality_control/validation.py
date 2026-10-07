"Validation of image-mask pair quality-control contracts"
import re
from geoai_dataset_curation.quality_control.contracts import (
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
)


FINDING_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)


def _is_sha256_id(value: object) -> bool:
    "Return whether a value is a canonical SHA-256 identity"
    if not isinstance(value, str):
        return False

    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(
            character in "0123456789abcdef"
            for character in digest
        )
    )


def validate_qc_finding(
    finding: QCFinding,
) -> tuple[str, ...]:
    "Return contract errors for one QC finding"
    errors: list[str] = []

    if (
        not isinstance(finding.code, str)
        or FINDING_CODE_PATTERN.fullmatch(
            finding.code
        )
        is None
    ):
        errors.append("code must be a lowercase machine-readable identifier.")

    if not isinstance(
        finding.severity,
        QCFindingSeverity,
    ):
        errors.append("severity must be a QCFindingSeverity.")

    if (
        not isinstance(finding.message, str)
        or not finding.message.strip()
    ):
        errors.append("message must not be empty.")
    return tuple(errors)


def validate_pair_qc_result(
    result: PairQCResult,
) -> tuple[str, ...]:
    "Return contract errors for one pair QC result"
    errors: list[str] = []
    if not _is_sha256_id(result.pair_id):
        errors.append("pair_id must be a valid SHA-256 identity.")

    if not _is_sha256_id(result.tile_id):
        errors.append("tile_id must be a valid SHA-256 identity.")

    if not isinstance(result.findings, tuple):
        errors.append("findings must be a tuple.")
        return tuple(errors)

    for index, finding in enumerate(result.findings):
        if not isinstance(finding, QCFinding):
            errors.append(
                f"findings[{index}] must be a QCFinding."
            )
            continue

        finding_errors = validate_qc_finding(finding)
        errors.extend(
            f"findings[{index}].{error}"
            for error in finding_errors
        )

    return tuple(errors)