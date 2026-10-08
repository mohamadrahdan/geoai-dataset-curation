"Stable identities for pair quality-control evidence"
from typing import Any
from geoai_dataset_curation.quality_control.contracts import (
    ImageBandStatistics,
    PairQCReport,
    PairVisualReview,
    QCFinding,
    VisualReviewCatalog,
)
from geoai_dataset_curation.tiling.identity import (
    _build_sha256_id,
)


def qc_finding_identity_payload(
    finding: QCFinding,
) -> dict[str, Any]:
    "Return the canonical identity payload for one finding"
    return {
        "code": finding.code,
        "severity": finding.severity.value,
        "message": finding.message,
    }


def image_band_statistics_identity_payload(
    statistics: ImageBandStatistics,
) -> dict[str, Any]:
    "Return the canonical identity payload for one image band"
    return {
        "band_index": statistics.band_index,
        "pixel_count": statistics.pixel_count,
        "finite_pixel_count": (
            statistics.finite_pixel_count
        ),
        "non_finite_pixel_count": (
            statistics.non_finite_pixel_count
        ),
        "minimum": statistics.minimum,
        "maximum": statistics.maximum,
        "mean": statistics.mean,
        "standard_deviation": (
            statistics.standard_deviation
        ),
    }


def pair_qc_report_identity_payload(
    report: PairQCReport,
) -> dict[str, Any]:
    "Return the canonical identity payload for one QC report"
    return {
        "schema_version": report.schema_version,
        "pair_catalog_id": report.pair_catalog_id,
        "traceability": {
            "pair_catalog_id": (
                report.traceability.pair_catalog_id
            ),
            "expected_pair_count": (
                report.traceability.expected_pair_count
            ),
            "verified_pair_count": (
                report.traceability.verified_pair_count
            ),
            "discovered_image_file_count": (
                report.traceability
                .discovered_image_file_count
            ),
            "discovered_mask_file_count": (
                report.traceability
                .discovered_mask_file_count
            ),
            "findings": [
                qc_finding_identity_payload(finding)
                for finding
                in report.traceability.findings
            ],
        },
        "pair_results": [
            {
                "pair_id": result.pair_id,
                "tile_id": result.tile_id,
                "findings": [
                    qc_finding_identity_payload(
                        finding
                    )
                    for finding in result.findings
                ],
            }
            for result in report.pair_results
        ],
        "image_statistics": [
            {
                "pair_id": item.pair_id,
                "tile_id": item.tile_id,
                "bands": [
                    image_band_statistics_identity_payload(
                        band
                    )
                    for band in item.bands
                ],
            }
            for item in report.image_statistics
        ],
    }


def build_pair_qc_report_id(
    report: PairQCReport,
) -> str:
    "Build a stable identifier for one pair QC report"
    return _build_sha256_id(
        pair_qc_report_identity_payload(report)
    )


def pair_visual_review_identity_payload(
    review: PairVisualReview,
) -> dict[str, Any]:
    "Return the canonical identity payload for one review"
    return {
        "pair_id": review.pair_id,
        "tile_id": review.tile_id,
        "status": review.status.value,
        "notes": review.notes,
    }


def visual_review_catalog_identity_payload(
    catalog: VisualReviewCatalog,
) -> dict[str, Any]:
    "Return the canonical identity payload for one review catalog"
    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "pair_catalog_id": catalog.pair_catalog_id,
        "reviewer": catalog.reviewer,
        "reviews": [
            pair_visual_review_identity_payload(
                review
            )
            for review in catalog.reviews
        ],
    }


def build_visual_review_catalog_id(
    catalog: VisualReviewCatalog,
) -> str:
    "Build a stable identifier for one visual-review catalog"
    return _build_sha256_id(
        visual_review_catalog_identity_payload(
            catalog
        )
    )