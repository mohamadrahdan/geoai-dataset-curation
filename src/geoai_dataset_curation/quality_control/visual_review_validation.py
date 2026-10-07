"Validation of human visual-review decisions"
from geoai_dataset_curation.quality_control.contracts import (
    PairVisualReview,
    VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
    VisualReviewCatalog,
    VisualReviewStatus,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    build_image_mask_pair_catalog_id,
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


def validate_pair_visual_review(
    review: PairVisualReview,
    *,
    pair: ImageMaskPairRecord,
) -> tuple[str, ...]:
    "Return contract errors for one human review"
    errors: list[str] = []

    if not _is_sha256_id(review.pair_id):
        errors.append("pair_id must be a valid SHA-256 identity.")
    elif review.pair_id != pair.pair_id:
        errors.append("pair_id must match the reviewed pair.")

    if not _is_sha256_id(review.tile_id):
        errors.append("tile_id must be a valid SHA-256 identity.")
    elif review.tile_id != pair.tile_id:
        errors.append("tile_id must match the reviewed pair.")

    status_is_valid = isinstance(
        review.status,
        VisualReviewStatus,
    )
    if not status_is_valid:
        errors.append("status must be a VisualReviewStatus.")

    if not isinstance(review.notes, str):
        errors.append("notes must be a string.")
    elif (
        status_is_valid
        and review.status in {
            VisualReviewStatus.REVIEW,
            VisualReviewStatus.FAIL,
        }
        and not review.notes.strip()
    ):
        errors.append("notes must explain REVIEW and FAIL decisions.")

    return tuple(errors)


def validate_visual_review_catalog(
    catalog: VisualReviewCatalog,
    *,
    pair_catalog: ImageMaskPairCatalog,
    require_complete: bool = False,
) -> tuple[str, ...]:
    "Return consistency errors for one visual-review catalog"
    errors: list[str] = []

    if (
        catalog.schema_version
        != VISUAL_REVIEW_CATALOG_SCHEMA_VERSION
    ):
        errors.append("schema_version is not supported.")

    if not isinstance(catalog.output_name, str) or not catalog.output_name.strip():
        errors.append("output_name must not be empty.")

    expected_pair_catalog_id = (
        build_image_mask_pair_catalog_id(
            pair_catalog
        )
    )
    if catalog.pair_catalog_id != expected_pair_catalog_id:
        errors.append("pair_catalog_id must match the pair catalog.")

    if not isinstance(catalog.reviewer, str) or not catalog.reviewer.strip():
        errors.append("reviewer must not be empty.")

    if not isinstance(catalog.reviews, tuple):
        errors.append("reviews must be a tuple.")
        return tuple(errors)

    expected_pair_ids = tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )
    observed_pair_ids = tuple(
        review.pair_id
        for review in catalog.reviews
        if isinstance(review, PairVisualReview)
    )

    if observed_pair_ids != expected_pair_ids:
        errors.append("reviews must cover every pair in catalog order.")

    if len(set(observed_pair_ids)) != len(observed_pair_ids):
        errors.append("review pair_id values must be unique.")

    pairs_by_id = {
        pair.pair_id: pair
        for pair in pair_catalog.pairs
    }

    for index, review in enumerate(catalog.reviews):
        if not isinstance(review, PairVisualReview):
            errors.append(f"reviews[{index}] must be a PairVisualReview.")
            continue

        pair = pairs_by_id.get(review.pair_id)
        if pair is None:
            continue

        review_errors = validate_pair_visual_review(
            review,
            pair=pair,
        )
        errors.extend(
            f"reviews[{index}].{error}"
            for error in review_errors
        )

    if require_complete and catalog.pending_count:
        errors.append("completed visual review must not contain PENDING decisions.")

    return tuple(errors)