"Persistence helpers for human visual-review catalogs"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.quality_control.contracts import (
    PairVisualReview,
    VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
    VisualReviewCatalog,
    VisualReviewStatus,
)
from geoai_dataset_curation.quality_control.visual_review_validation import (
    validate_visual_review_catalog,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    build_image_mask_pair_catalog_id,
)


def build_visual_review_template(
    pair_catalog: ImageMaskPairCatalog,
    *,
    output_name: str,
    reviewer: str,
) -> VisualReviewCatalog:
    "Build a pending human-review record for every pair"
    if not output_name.strip():
        raise ValueError("output_name must not be empty.")

    if not reviewer.strip():
        raise ValueError("reviewer must not be empty.")

    catalog = VisualReviewCatalog(
        schema_version=VISUAL_REVIEW_CATALOG_SCHEMA_VERSION,
        output_name=output_name,
        pair_catalog_id=build_image_mask_pair_catalog_id(pair_catalog),
        reviewer=reviewer,
        reviews=tuple(
            PairVisualReview(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                status=VisualReviewStatus.PENDING,
            )
            for pair in pair_catalog.pairs
        ),
    )

    errors = validate_visual_review_catalog(catalog, pair_catalog=pair_catalog)
    if errors:
        message = "Cannot build invalid visual-review template: " + "; ".join(errors)
        raise ValueError(message)

    return catalog


def visual_review_catalog_to_dict(
    catalog: VisualReviewCatalog,
    *,
    pair_catalog: ImageMaskPairCatalog,
    require_complete: bool = False,
) -> dict[str, Any]:
    "Serialize one validated visual-review catalog"
    errors = validate_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
        require_complete=require_complete,
    )
    if errors:
        message = "Cannot serialize invalid visual-review catalog: " + "; ".join(errors)
        raise ValueError(message)

    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "pair_catalog_id": catalog.pair_catalog_id,
        "reviewer": catalog.reviewer,
        "reviews": [
            {
                "pair_id": review.pair_id,
                "tile_id": review.tile_id,
                "status": review.status.value,
                "notes": review.notes,
            }
            for review in catalog.reviews
        ],
    }


def visual_review_catalog_from_dict(
    payload: dict[str, Any],
) -> VisualReviewCatalog:
    "Deserialize one visual-review catalog payload"
    try:
        reviews = tuple(
            PairVisualReview(
                pair_id=str(item["pair_id"]),
                tile_id=str(item["tile_id"]),
                status=VisualReviewStatus(str(item["status"])),
                notes=str(item.get("notes", "")),
            )
            for item in payload["reviews"]
        )

        return VisualReviewCatalog(
            schema_version=str(payload["schema_version"]),
            output_name=str(payload["output_name"]),
            pair_catalog_id=str(payload["pair_catalog_id"]),
            reviewer=str(payload["reviewer"]),
            reviews=reviews,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid visual-review catalog payload.") from error


def write_visual_review_catalog(
    catalog: VisualReviewCatalog,
    *,
    pair_catalog: ImageMaskPairCatalog,
    output_path: Path,
    require_complete: bool = False,
) -> Path:
    "Write one canonical visual-review JSON artifact"
    payload = visual_review_catalog_to_dict(
        catalog,
        pair_catalog=pair_catalog,
        require_complete=require_complete,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return output_path


def read_visual_review_catalog(
    artifact_path: Path,
    *,
    pair_catalog: ImageMaskPairCatalog,
    require_complete: bool = False,
) -> VisualReviewCatalog:
    "Read and validate one visual-review JSON artifact"
    try:
        payload = json.loads(
            artifact_path.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Visual-review artifact is not readable JSON.") from error

    if not isinstance(payload, dict):
        raise ValueError("Visual-review artifact root must be an object.")

    catalog = visual_review_catalog_from_dict(payload)
    errors = validate_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
        require_complete=require_complete,
    )
    if errors:
        message = "Visual-review artifact is invalid: " + "; ".join(errors)
        raise ValueError(message)
    return catalog


def verify_visual_review_catalog_artifact(
    expected: VisualReviewCatalog,
    *,
    pair_catalog: ImageMaskPairCatalog,
    artifact_path: Path,
    require_complete: bool = False,
) -> tuple[str, ...]:
    "Verify persisted visual-review content against memory"
    if not artifact_path.is_file():
        return ("visual-review artifact does not exist.",)

    try:
        observed = read_visual_review_catalog(
            artifact_path,
            pair_catalog=pair_catalog,
            require_complete=require_complete,
        )
    except ValueError as error:
        return (str(error),)

    if observed != expected:
        return ("visual-review artifact content does not match the expected catalog.",)

    return ()