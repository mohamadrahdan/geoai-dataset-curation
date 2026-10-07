"Automated pair quality-control execution and reporting"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.quality_control.contracts import (
    ImageBandStatistics,
    PAIR_QC_REPORT_SCHEMA_VERSION,
    PairImageStatistics,
    PairQCReport,
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
)
from geoai_dataset_curation.quality_control.image_content import inspect_pair_image_content
from geoai_dataset_curation.quality_control.mask_semantics import inspect_pair_mask_semantics
from geoai_dataset_curation.quality_control.raster_integrity import inspect_pair_raster_integrity
from geoai_dataset_curation.quality_control.traceability import inspect_cross_artifact_traceability
from geoai_dataset_curation.quality_control.validation import validate_pair_qc_result
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.tiling import TileCatalog


def _merge_findings(*groups: tuple[QCFinding, ...]) -> tuple[QCFinding, ...]:
    "Merge findings while preserving order and removing duplicates"
    return tuple(dict.fromkeys(finding for group in groups for finding in group))


def run_pair_quality_control(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
    expected_image_band_count: int,
    expected_image_dtype: str,
) -> PairQCReport:
    "Run automated QC over every physical image-mask pair"
    traceability = inspect_cross_artifact_traceability(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    candidates_by_id = {candidate.tile_id: candidate for candidate in selection.selected_candidates}
    pair_results: list[PairQCResult] = []
    image_statistics: list[PairImageStatistics] = []

    for pair in pair_catalog.pairs:
        candidate = candidates_by_id.get(pair.tile_id)

        if candidate is None:
            result = PairQCResult(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                findings=(
                    QCFinding(
                        code="qc.candidate_missing",
                        severity=QCFindingSeverity.ERROR,
                        message="Pair does not have a selected candidate.",
                    ),
                ),
            )
            pair_results.append(result)
            image_statistics.append(PairImageStatistics(pair_id=pair.pair_id, tile_id=pair.tile_id, bands=()))
            continue

        raster_result = inspect_pair_raster_integrity(
            pair,
            candidate=candidate,
            expected_image_band_count=expected_image_band_count,
            expected_image_dtype=expected_image_dtype,
        )
        mask_result = inspect_pair_mask_semantics(pair, candidate=candidate)
        image_inspection = inspect_pair_image_content(pair)
        findings = _merge_findings(
            raster_result.findings,
            mask_result.findings,
            image_inspection.pair_result.findings,
        )
        result = PairQCResult(pair_id=pair.pair_id, tile_id=pair.tile_id, findings=findings)
        result_errors = validate_pair_qc_result(result)

        if result_errors:
            message = "Automated QC produced an invalid pair result: " + "; ".join(result_errors)
            raise RuntimeError(message)

        pair_results.append(result)
        image_statistics.append(
            PairImageStatistics(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                bands=image_inspection.band_statistics,
            )
        )

    return PairQCReport(
        schema_version=PAIR_QC_REPORT_SCHEMA_VERSION,
        pair_catalog_id=build_image_mask_pair_catalog_id(pair_catalog),
        traceability=traceability,
        pair_results=tuple(pair_results),
        image_statistics=tuple(image_statistics),
    )


def _finding_to_dict(finding: QCFinding) -> dict[str, Any]:
    return {
        "code": finding.code,
        "severity": finding.severity.value,
        "message": finding.message,
    }


def _band_statistics_to_dict(statistics: ImageBandStatistics) -> dict[str, Any]:
    return {
        "band_index": statistics.band_index,
        "pixel_count": statistics.pixel_count,
        "finite_pixel_count": statistics.finite_pixel_count,
        "non_finite_pixel_count": statistics.non_finite_pixel_count,
        "minimum": statistics.minimum,
        "maximum": statistics.maximum,
        "mean": statistics.mean,
        "standard_deviation": statistics.standard_deviation,
        "is_constant": statistics.is_constant,
    }


def pair_qc_report_to_dict(report: PairQCReport) -> dict[str, Any]:
    "Serialize one automated pair QC report"
    statistics_by_pair_id = {item.pair_id: item for item in report.image_statistics}

    return {
        "schema_version": report.schema_version,
        "pair_catalog_id": report.pair_catalog_id,
        "status": report.status.value,
        "summary": {
            "pair_count": report.pair_count,
            "pass_count": report.pass_count,
            "warning_count": report.warning_count,
            "fail_count": report.fail_count,
            "finding_count": report.finding_count,
        },
        "traceability": {
            "status": report.traceability.status.value,
            "expected_pair_count": report.traceability.expected_pair_count,
            "verified_pair_count": report.traceability.verified_pair_count,
            "discovered_image_file_count": report.traceability.discovered_image_file_count,
            "discovered_mask_file_count": report.traceability.discovered_mask_file_count,
            "findings": [_finding_to_dict(finding) for finding in report.traceability.findings],
        },
        "pairs": [
            {
                "pair_id": result.pair_id,
                "tile_id": result.tile_id,
                "status": result.status.value,
                "findings": [_finding_to_dict(finding) for finding in result.findings],
                "band_statistics": [
                    _band_statistics_to_dict(statistics)
                    for statistics in statistics_by_pair_id[result.pair_id].bands
                ],
            }
            for result in report.pair_results
        ],
    }


def write_pair_qc_report(report: PairQCReport, output_path: Path) -> Path:
    "Write one deterministic automated QC report"
    payload = pair_qc_report_to_dict(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path