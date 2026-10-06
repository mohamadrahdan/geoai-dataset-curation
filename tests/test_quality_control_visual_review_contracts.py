from dataclasses import replace
from geoai_dataset_curation.quality_control import (
    QCStatus,
    PairVisualReview,
    VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
    VisualReviewCatalog,
    VisualReviewStatus,
    validate_pair_visual_review,
    validate_visual_review_catalog,
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.tiling import TileLabelClass


def make_pair(
    digest_character: str,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id="sha256:" + (digest_character * 64),
        tile_id="sha256:" + (digest_character * 64),
        image_tile_path=f"images/{digest_character}.tif",
        mask_tile_path=f"masks/{digest_character}.tif",
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=NegativeProvenanceKind.NONE,
    )


def make_pair_catalog() -> ImageMaskPairCatalog:
    return ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="review-pairs",
        tile_catalog_id="sha256:" + ("c" * 64),
        selection_id="sha256:" + ("d" * 64),
        provenance_catalog_id="sha256:" + ("e" * 64),
        source_image_artifact_path="source-image.tif",
        source_label_artifact_path="source-label.tif",
        pairs=(
            make_pair("a"),
            make_pair("b"),
        ),
    )


def make_review(
    pair: ImageMaskPairRecord,
    *,
    status: VisualReviewStatus,
    notes: str = "",
) -> PairVisualReview:
    return PairVisualReview(
        pair_id=pair.pair_id,
        tile_id=pair.tile_id,
        status=status,
        notes=notes,
    )


def make_review_catalog(
    *,
    statuses: tuple[
        VisualReviewStatus,
        VisualReviewStatus,
    ],
    notes: tuple[str, str] = ("", ""),
) -> VisualReviewCatalog:
    pair_catalog = make_pair_catalog()

    return VisualReviewCatalog(
        schema_version=VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
        output_name="visual-review-v1",
        pair_catalog_id=build_image_mask_pair_catalog_id(
            pair_catalog
        ),
        reviewer="test-reviewer",
        reviews=tuple(
            make_review(
                pair,
                status=status,
                notes=review_notes,
            )
            for pair, status, review_notes in zip(
                pair_catalog.pairs,
                statuses,
                notes,
                strict=True,
            )
        ),
    )


def test_pending_review_catalog_is_incomplete() -> None:
    pair_catalog = make_pair_catalog()
    catalog = make_review_catalog(
        statuses=(
            VisualReviewStatus.PENDING,
            VisualReviewStatus.PENDING,
        )
    )
    assert catalog.is_complete is False
    assert catalog.status == QCStatus.WARNING
    assert catalog.pending_count == 2
    assert validate_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
    ) == ()
    assert validate_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
        require_complete=True,
    ) == (
        "completed visual review must not contain PENDING decisions.",
    )


def test_completed_pass_catalog_passes() -> None:
    pair_catalog = make_pair_catalog()
    catalog = make_review_catalog(
        statuses=(
            VisualReviewStatus.PASS,
            VisualReviewStatus.PASS,
        )
    )
    assert catalog.is_complete is True
    assert catalog.status == QCStatus.PASS
    assert catalog.pass_count == 2
    assert validate_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
        require_complete=True,
    ) == ()


def test_review_decision_requires_notes() -> None:
    pair = make_pair("a")
    review = make_review(
        pair,
        status=VisualReviewStatus.REVIEW,
    )
    assert validate_pair_visual_review(
        review,
        pair=pair,
    ) == ("notes must explain REVIEW and FAIL decisions.",)


def test_fail_decision_requires_notes() -> None:
    pair = make_pair("a")
    review = make_review(
        pair,
        status=VisualReviewStatus.FAIL,
    )

    assert validate_pair_visual_review(
        review,
        pair=pair,
    ) == ("notes must explain REVIEW and FAIL decisions.",)


def test_review_catalog_must_preserve_pair_order() -> None:
    pair_catalog = make_pair_catalog()
    catalog = make_review_catalog(
        statuses=(
            VisualReviewStatus.PASS,
            VisualReviewStatus.PASS,
        )
    )
    reversed_catalog = replace(
        catalog,
        reviews=tuple(
            reversed(catalog.reviews)
        ),
    )

    errors = validate_visual_review_catalog(
        reversed_catalog,
        pair_catalog=pair_catalog,
    )

    assert ("reviews must cover every pair in catalog order."
        in errors
    )


def test_review_catalog_rejects_duplicate_pair_ids() -> None:
    pair_catalog = make_pair_catalog()
    catalog = make_review_catalog(
        statuses=(
            VisualReviewStatus.PASS,
            VisualReviewStatus.PASS,
        )
    )
    duplicate_catalog = replace(
        catalog,
        reviews=(
            catalog.reviews[0],
            catalog.reviews[0],
        ),
    )

    errors = validate_visual_review_catalog(
        duplicate_catalog,
        pair_catalog=pair_catalog,
    )
    assert "review pair_id values must be unique." in errors