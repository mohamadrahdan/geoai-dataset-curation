import json
from dataclasses import replace
from pathlib import Path
import pytest
from geoai_dataset_curation.quality_control import (
    VisualReviewStatus,
    build_visual_review_template,
    read_visual_review_catalog,
    verify_visual_review_catalog_artifact,
    visual_review_catalog_to_dict,
    write_visual_review_catalog,
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
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


def complete_catalog(catalog):
    return replace(
        catalog,
        reviews=tuple(
            replace(
                review,
                status=VisualReviewStatus.PASS,
            )
            for review in catalog.reviews
        ),
    )


def test_visual_review_template_covers_every_pair() -> None:
    pair_catalog = make_pair_catalog()

    catalog = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )
    assert catalog.review_count == 2
    assert catalog.pending_count == 2
    assert tuple(
        review.pair_id
        for review in catalog.reviews
    ) == tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )


def test_visual_review_catalog_serializes_for_editing() -> None:
    pair_catalog = make_pair_catalog()
    catalog = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )

    payload = visual_review_catalog_to_dict(
        catalog,
        pair_catalog=pair_catalog,
    )
    assert payload["reviewer"] == "test-reviewer"
    assert [
        review["status"]
        for review in payload["reviews"]
    ] == [
        "pending",
        "pending",
    ]


def test_visual_review_catalog_round_trip(
    tmp_path: Path,
) -> None:
    pair_catalog = make_pair_catalog()
    catalog = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )
    artifact_path = tmp_path / "visual-review.json"

    write_visual_review_catalog(
        catalog,
        pair_catalog=pair_catalog,
        output_path=artifact_path,
    )
    observed = read_visual_review_catalog(
        artifact_path,
        pair_catalog=pair_catalog,
    )
    assert observed == catalog


def test_complete_review_is_required_for_final_read(
    tmp_path: Path,
) -> None:
    pair_catalog = make_pair_catalog()
    template = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )
    completed = complete_catalog(template)
    artifact_path = tmp_path / "visual-review.json"

    write_visual_review_catalog(
        completed,
        pair_catalog=pair_catalog,
        output_path=artifact_path,
        require_complete=True,
    )
    observed = read_visual_review_catalog(
        artifact_path,
        pair_catalog=pair_catalog,
        require_complete=True,
    )
    assert observed == completed
    assert observed.is_complete is True


def test_pending_review_is_rejected_when_completion_is_required(
    tmp_path: Path,
) -> None:
    pair_catalog = make_pair_catalog()
    template = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )

    with pytest.raises(
        ValueError,
        match="PENDING",
    ):
        write_visual_review_catalog(
            template,
            pair_catalog=pair_catalog,
            output_path=tmp_path / "visual-review.json",
            require_complete=True,
        )


def test_invalid_review_status_is_rejected(
    tmp_path: Path,
) -> None:
    pair_catalog = make_pair_catalog()
    template = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )
    payload = visual_review_catalog_to_dict(
        template,
        pair_catalog=pair_catalog,
    )
    payload["reviews"][0]["status"] = "unknown"
    artifact_path = tmp_path / "visual-review.json"
    artifact_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid visual-review catalog payload",
    ):
        read_visual_review_catalog(
            artifact_path,
            pair_catalog=pair_catalog,
        )


def test_modified_review_artifact_is_detected(
    tmp_path: Path,
) -> None:
    pair_catalog = make_pair_catalog()
    expected = build_visual_review_template(
        pair_catalog,
        output_name="visual-review-v1",
        reviewer="test-reviewer",
    )
    modified = replace(
        expected,
        reviewer="different-reviewer",
    )
    artifact_path = tmp_path / "visual-review.json"

    write_visual_review_catalog(
        modified,
        pair_catalog=pair_catalog,
        output_path=artifact_path,
    )
    assert verify_visual_review_catalog_artifact(
        expected,
        pair_catalog=pair_catalog,
        artifact_path=artifact_path,
    ) == (
        "visual-review artifact content does not match the expected catalog.",
    )