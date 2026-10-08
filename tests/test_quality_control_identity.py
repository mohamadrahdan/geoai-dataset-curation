from dataclasses import replace
from geoai_dataset_curation.quality_control import (
    PAIR_QC_REPORT_SCHEMA_VERSION,
    VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
    ImageBandStatistics,
    PairImageStatistics,
    PairQCReport,
    PairQCResult,
    PairVisualReview,
    QCFinding,
    QCFindingSeverity,
    TraceabilityQCResult,
    VisualReviewCatalog,
    VisualReviewStatus,
    build_pair_qc_report_id,
    build_visual_review_catalog_id,
    pair_qc_report_identity_payload,
    visual_review_catalog_identity_payload,
)


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)
PAIR_CATALOG_ID = "sha256:" + ("c" * 64)


def make_qc_report() -> PairQCReport:
    return PairQCReport(
        schema_version=(
            PAIR_QC_REPORT_SCHEMA_VERSION
        ),
        pair_catalog_id=PAIR_CATALOG_ID,
        traceability=TraceabilityQCResult(
            pair_catalog_id=PAIR_CATALOG_ID,
            expected_pair_count=1,
            verified_pair_count=1,
            discovered_image_file_count=1,
            discovered_mask_file_count=1,
            findings=(),
        ),
        pair_results=(
            PairQCResult(
                pair_id=PAIR_ID,
                tile_id=TILE_ID,
                findings=(),
            ),
        ),
        image_statistics=(
            PairImageStatistics(
                pair_id=PAIR_ID,
                tile_id=TILE_ID,
                bands=(
                    ImageBandStatistics(
                        band_index=1,
                        pixel_count=16,
                        finite_pixel_count=16,
                        non_finite_pixel_count=0,
                        minimum=1.0,
                        maximum=4.0,
                        mean=2.5,
                        standard_deviation=1.0,
                    ),
                ),
            ),
        ),
    )


def make_visual_review_catalog(
) -> VisualReviewCatalog:
    return VisualReviewCatalog(
        schema_version=(
            VISUAL_REVIEW_CATALOG_SCHEMA_VERSION
        ),
        output_name="visual-review-v1",
        pair_catalog_id=PAIR_CATALOG_ID,
        reviewer="test-reviewer",
        reviews=(
            PairVisualReview(
                pair_id=PAIR_ID,
                tile_id=TILE_ID,
                status=VisualReviewStatus.PASS,
                notes="Pair accepted.",
            ),
        ),
    )


def test_pair_qc_report_identity_is_deterministic(
) -> None:
    report = make_qc_report()

    first_id = build_pair_qc_report_id(report)
    second_id = build_pair_qc_report_id(report)

    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_pair_qc_report_identity_covers_findings(
) -> None:
    report = make_qc_report()

    changed_result = replace(
        report.pair_results[0],
        findings=(
            QCFinding(
                code="image.changed",
                severity=(
                    QCFindingSeverity.WARNING
                ),
                message="Changed finding.",
            ),
        ),
    )
    changed_report = replace(
        report,
        pair_results=(changed_result,),
    )

    assert build_pair_qc_report_id(
        changed_report
    ) != build_pair_qc_report_id(report)


def test_pair_qc_report_identity_covers_statistics(
) -> None:
    report = make_qc_report()

    changed_band = replace(
        report.image_statistics[0].bands[0],
        mean=3.0,
    )
    changed_statistics = replace(
        report.image_statistics[0],
        bands=(changed_band,),
    )
    changed_report = replace(
        report,
        image_statistics=(changed_statistics,),
    )

    assert build_pair_qc_report_id(
        changed_report
    ) != build_pair_qc_report_id(report)


def test_pair_qc_report_payload_is_semantic(
) -> None:
    payload = pair_qc_report_identity_payload(
        make_qc_report()
    )

    assert payload["schema_version"] == (
        PAIR_QC_REPORT_SCHEMA_VERSION
    )
    assert (
        payload["pair_catalog_id"]
        == PAIR_CATALOG_ID
    )
    assert (
        payload["pair_results"][0]["pair_id"]
        == PAIR_ID
    )


def test_visual_review_identity_is_deterministic(
) -> None:
    catalog = make_visual_review_catalog()

    first_id = build_visual_review_catalog_id(
        catalog
    )
    second_id = build_visual_review_catalog_id(
        catalog
    )

    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_visual_review_identity_covers_decision(
) -> None:
    catalog = make_visual_review_catalog()

    changed_review = replace(
        catalog.reviews[0],
        status=VisualReviewStatus.REVIEW,
        notes="Requires another review.",
    )
    changed_catalog = replace(
        catalog,
        reviews=(changed_review,),
    )

    assert build_visual_review_catalog_id(
        changed_catalog
    ) != build_visual_review_catalog_id(
        catalog
    )


def test_visual_review_identity_covers_reviewer(
) -> None:
    catalog = make_visual_review_catalog()
    changed_catalog = replace(
        catalog,
        reviewer="another-reviewer",
    )

    assert build_visual_review_catalog_id(
        changed_catalog
    ) != build_visual_review_catalog_id(
        catalog
    )


def test_visual_review_payload_is_semantic(
) -> None:
    payload = (
        visual_review_catalog_identity_payload(
            make_visual_review_catalog()
        )
    )

    assert payload["schema_version"] == (
        VISUAL_REVIEW_CATALOG_SCHEMA_VERSION
    )
    assert (
        payload["pair_catalog_id"]
        == PAIR_CATALOG_ID
    )
    assert (
        payload["reviews"][0]["status"]
        == "pass"
    )