"Pre-split acceptance gate for quality-controlled pairs"
from geoai_dataset_curation.quality_control import (
    PAIR_QC_REPORT_SCHEMA_VERSION,
    QCStatus,
    PairQCReport,
    VisualReviewCatalog,
    build_pair_qc_report_id,
    build_visual_review_catalog_id,
    validate_visual_review_catalog,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split.contracts import (
    SpatialSplitInputAcceptance,
)


def validate_spatial_split_input_gate(
    pair_catalog: ImageMaskPairCatalog,
    *,
    qc_report: PairQCReport,
    visual_review_catalog: VisualReviewCatalog,
) -> tuple[str, ...]:
    "Return errors preventing a pair population from splitting"
    errors: list[str] = []

    pair_catalog_id = (
        build_image_mask_pair_catalog_id(
            pair_catalog
        )
    )
    pair_count = pair_catalog.pair_count

    if (
        qc_report.schema_version
        != PAIR_QC_REPORT_SCHEMA_VERSION
    ):
        errors.append(
            "automated QC report schema_version "
            "is not supported."
        )

    if (
        qc_report.pair_catalog_id
        != pair_catalog_id
    ):
        errors.append(
            "automated QC report pair_catalog_id "
            "must match the pair catalog."
        )

    if (
        qc_report.traceability.pair_catalog_id
        != pair_catalog_id
    ):
        errors.append(
            "traceability pair_catalog_id must "
            "match the pair catalog."
        )

    if qc_report.status != QCStatus.PASS:
        errors.append("automated QC report status must be pass.")

    if (
        qc_report.traceability.status
        != QCStatus.PASS
    ):
        errors.append("traceability status must be pass.")

    if (
        qc_report.traceability
        .expected_pair_count
        != pair_count
    ):
        errors.append(
            "traceability expected_pair_count must "
            "match the pair catalog."
        )

    if (
        qc_report.traceability
        .verified_pair_count
        != pair_count
    ):
        errors.append(
            "traceability verified_pair_count must "
            "match the pair catalog."
        )

    if (
        qc_report.traceability
        .discovered_image_file_count
        != pair_count
    ):
        errors.append(
            "traceability discovered_image_file_count "
            "must match the pair catalog."
        )

    if (
        qc_report.traceability
        .discovered_mask_file_count
        != pair_count
    ):
        errors.append(
            "traceability discovered_mask_file_count "
            "must match the pair catalog."
        )

    if qc_report.pass_count != pair_count:
        errors.append("automated QC must pass every pair.")

    if qc_report.warning_count != 0:
        errors.append("automated QC must not contain warnings.")

    if qc_report.fail_count != 0:
        errors.append("automated QC must not contain failures.")

    if qc_report.finding_count != 0:
        errors.append("automated QC must not contain findings.")

    expected_pair_ids = tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )
    expected_tile_ids = tuple(
        pair.tile_id
        for pair in pair_catalog.pairs
    )

    result_pair_ids = tuple(
        result.pair_id
        for result in qc_report.pair_results
    )
    result_tile_ids = tuple(
        result.tile_id
        for result in qc_report.pair_results
    )

    if result_pair_ids != expected_pair_ids:
        errors.append(
            "automated QC pair results must cover "
            "every pair in catalog order."
        )

    if result_tile_ids != expected_tile_ids:
        errors.append(
            "automated QC result tile_id values "
            "must match the pair catalog."
        )

    statistics_pair_ids = tuple(
        statistics.pair_id
        for statistics
        in qc_report.image_statistics
    )
    statistics_tile_ids = tuple(
        statistics.tile_id
        for statistics
        in qc_report.image_statistics
    )

    if statistics_pair_ids != expected_pair_ids:
        errors.append(
            "image statistics must cover every pair "
            "in catalog order."
        )

    if statistics_tile_ids != expected_tile_ids:
        errors.append(
            "image-statistics tile_id values must "
            "match the pair catalog."
        )

    review_errors = (
        validate_visual_review_catalog(
            visual_review_catalog,
            pair_catalog=pair_catalog,
            require_complete=True,
        )
    )
    errors.extend(
        f"visual_review.{error}"
        for error in review_errors
    )

    if (
        visual_review_catalog.status
        != QCStatus.PASS
    ):
        errors.append("visual review status must be pass.")

    if (
        visual_review_catalog.pass_count
        != pair_count
    ):
        errors.append("human review must pass every pair.")

    if visual_review_catalog.pending_count != 0:
        errors.append(
            "human review must not contain "
            "pending decisions."
        )

    if (
        visual_review_catalog
        .review_required_count
        != 0
    ):
        errors.append(
            "human review must not contain "
            "review-required decisions."
        )

    if visual_review_catalog.fail_count != 0:
        errors.append(
            "human review must not contain "
            "failed decisions."
        )

    return tuple(errors)


def accept_spatial_split_inputs(
    pair_catalog: ImageMaskPairCatalog,
    *,
    qc_report: PairQCReport,
    visual_review_catalog: VisualReviewCatalog,
) -> SpatialSplitInputAcceptance:
    "Accept one pair population or reject it before splitting"
    errors = validate_spatial_split_input_gate(
        pair_catalog,
        qc_report=qc_report,
        visual_review_catalog=(
            visual_review_catalog
        ),
    )
    if errors:
        raise ValueError(
            "Pair population is not eligible for "
            "spatial splitting: "
            + "; ".join(errors)
        )

    return SpatialSplitInputAcceptance(
        pair_catalog_id=(
            build_image_mask_pair_catalog_id(
                pair_catalog
            )
        ),
        pair_qc_report_id=(
            build_pair_qc_report_id(
                qc_report
            )
        ),
        visual_review_catalog_id=(
            build_visual_review_catalog_id(
                visual_review_catalog
            )
        ),
        pair_ids=tuple(
            pair.pair_id
            for pair in pair_catalog.pairs
        ),
        tile_ids=tuple(
            pair.tile_id
            for pair in pair_catalog.pairs
        ),
    )