from dataclasses import replace
import pytest
from geoai_dataset_curation.quality_control import (
    PAIR_QC_REPORT_SCHEMA_VERSION,
    VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
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
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split import (
    accept_spatial_split_inputs,
    validate_spatial_split_input_gate,
)
from geoai_dataset_curation.tiling import (
    TileLabelClass,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_pair(
    pair_character: str,
    tile_character: str,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=sha(pair_character),
        tile_id=sha(tile_character),
        image_tile_path=(
            f"images/{pair_character}.tif"
        ),
        mask_tile_path=(
            f"masks/{pair_character}.tif"
        ),
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=(
            NegativeProvenanceKind.NONE
        ),
    )


def make_pair_catalog() -> ImageMaskPairCatalog:
    return ImageMaskPairCatalog(
        schema_version=(
            IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION
        ),
        output_name="pairs-v1",
        tile_catalog_id=sha("a"),
        selection_id=sha("b"),
        provenance_catalog_id=sha("c"),
        source_image_artifact_path=(
            "source-image.tif"
        ),
        source_label_artifact_path=(
            "source-label.tif"
        ),
        pairs=(
            make_pair("1", "4"),
            make_pair("2", "5"),
        ),
    )


def make_qc_report(
    pair_catalog: ImageMaskPairCatalog,
) -> PairQCReport:
    pair_catalog_id = (
        build_image_mask_pair_catalog_id(
            pair_catalog
        )
    )

    return PairQCReport(
        schema_version=(
            PAIR_QC_REPORT_SCHEMA_VERSION
        ),
        pair_catalog_id=pair_catalog_id,
        traceability=TraceabilityQCResult(
            pair_catalog_id=pair_catalog_id,
            expected_pair_count=2,
            verified_pair_count=2,
            discovered_image_file_count=2,
            discovered_mask_file_count=2,
            findings=(),
        ),
        pair_results=tuple(
            PairQCResult(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                findings=(),
            )
            for pair in pair_catalog.pairs
        ),
        image_statistics=tuple(
            PairImageStatistics(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                bands=(),
            )
            for pair in pair_catalog.pairs
        ),
    )


def make_visual_review_catalog(
    pair_catalog: ImageMaskPairCatalog,
) -> VisualReviewCatalog:
    return VisualReviewCatalog(
        schema_version=(
            VISUAL_REVIEW_CATALOG_SCHEMA_VERSION
        ),
        output_name="visual-review-v1",
        pair_catalog_id=(
            build_image_mask_pair_catalog_id(
                pair_catalog
            )
        ),
        reviewer="test-reviewer",
        reviews=tuple(
            PairVisualReview(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                status=VisualReviewStatus.PASS,
                notes="Accepted.",
            )
            for pair in pair_catalog.pairs
        ),
    )


def make_context() -> tuple[
    ImageMaskPairCatalog,
    PairQCReport,
    VisualReviewCatalog,
]:
    pair_catalog = make_pair_catalog()
    return (
        pair_catalog,
        make_qc_report(pair_catalog),
        make_visual_review_catalog(
            pair_catalog
        ),
    )


def test_complete_pass_population_is_accepted(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    assert validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=qc_report,
        visual_review_catalog=reviews,
    ) == ()

    acceptance = accept_spatial_split_inputs(
        pair_catalog,
        qc_report=qc_report,
        visual_review_catalog=reviews,
    )

    assert acceptance.pair_count == 2
    assert acceptance.pair_catalog_id == (
        build_image_mask_pair_catalog_id(
            pair_catalog
        )
    )
    assert acceptance.pair_qc_report_id == (
        build_pair_qc_report_id(
            qc_report
        )
    )
    assert (
        acceptance.visual_review_catalog_id
        == build_visual_review_catalog_id(
            reviews
        )
    )
    assert acceptance.pair_ids == tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )
    assert acceptance.tile_ids == tuple(
        pair.tile_id
        for pair in pair_catalog.pairs
    )


def test_automated_warning_blocks_the_population(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    warning_result = replace(
        qc_report.pair_results[0],
        findings=(
            QCFinding(
                code="image.constant_band",
                severity=(
                    QCFindingSeverity.WARNING
                ),
                message="Constant band.",
            ),
        ),
    )
    warning_report = replace(
        qc_report,
        pair_results=(
            warning_result,
            qc_report.pair_results[1],
        ),
    )

    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=warning_report,
        visual_review_catalog=reviews,
    )

    assert (
        "automated QC report status must be pass."
        in errors
    )
    assert (
        "automated QC must not contain warnings."
        in errors
    )
    assert (
        "automated QC must not contain findings."
        in errors
    )


def test_incomplete_traceability_blocks_population(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    incomplete_traceability = replace(
        qc_report.traceability,
        verified_pair_count=1,
    )
    invalid_report = replace(
        qc_report,
        traceability=incomplete_traceability,
    )

    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=invalid_report,
        visual_review_catalog=reviews,
    )

    assert (
        "traceability verified_pair_count must "
        "match the pair catalog."
        in errors
    )


def test_reordered_qc_results_are_rejected(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    reordered_report = replace(
        qc_report,
        pair_results=tuple(
            reversed(
                qc_report.pair_results
            )
        ),
    )

    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=reordered_report,
        visual_review_catalog=reviews,
    )

    assert (
        "automated QC pair results must cover "
        "every pair in catalog order."
        in errors
    )


def test_incomplete_statistics_are_rejected(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    incomplete_report = replace(
        qc_report,
        image_statistics=(
            qc_report.image_statistics[0],
        ),
    )

    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=incomplete_report,
        visual_review_catalog=reviews,
    )

    assert (
        "image statistics must cover every pair "
        "in catalog order."
        in errors
    )


@pytest.mark.parametrize(
    "status",
    (
        VisualReviewStatus.PENDING,
        VisualReviewStatus.REVIEW,
        VisualReviewStatus.FAIL,
    ),
)
def test_non_pass_human_decision_blocks_population(
    status: VisualReviewStatus,
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    changed_review = replace(
        reviews.reviews[0],
        status=status,
        notes="Not accepted.",
    )
    invalid_reviews = replace(
        reviews,
        reviews=(
            changed_review,
            reviews.reviews[1],
        ),
    )

    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=qc_report,
        visual_review_catalog=invalid_reviews,
    )

    assert (
        "visual review status must be pass."
        in errors
    )
    assert (
        "human review must pass every pair."
        in errors
    )


def test_rejected_population_raises_value_error(
) -> None:
    pair_catalog, qc_report, reviews = (
        make_context()
    )

    pending_review = replace(
        reviews.reviews[0],
        status=VisualReviewStatus.PENDING,
    )
    pending_catalog = replace(
        reviews,
        reviews=(
            pending_review,
            reviews.reviews[1],
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Pair population is not eligible "
            "for spatial splitting"
        ),
    ):
        accept_spatial_split_inputs(
            pair_catalog,
            qc_report=qc_report,
            visual_review_catalog=(
                pending_catalog
            ),
        )