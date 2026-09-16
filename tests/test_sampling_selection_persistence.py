import json
from pathlib import Path
from geoai_dataset_curation.sampling import (
    LOOP1_SAMPLING_POLICY,
    TILE_SAMPLING_SELECTION_SCHEMA_VERSION,
    build_tile_sampling_selection_id,
    sampling_policy_identity_payload,
    select_tile_candidates,
    tile_sampling_selection_identity_payload,
    tile_sampling_selection_to_dict,
    verify_tile_sampling_selection_artifact,
    write_tile_sampling_selection_catalog,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    label_class: TileLabelClass,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 0, 15),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 15),
        TileLabelClass.ALL_IGNORE: (0, 0, 16),
    }
    positive, negative, ignore = counts[label_class]
    left = float(row_index * 40)
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 4,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=left,
        bottom=0.0,
        right=left + 40.0,
        top=40.0,
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def make_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="sampling-candidates",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(
            make_candidate(
                digest_character="c",
                row_index=0,
                label_class=TileLabelClass.POSITIVE,
            ),
            make_candidate(
                digest_character="d",
                row_index=1,
                label_class=TileLabelClass.ALL_IGNORE,
            ),
            make_candidate(
                digest_character="e",
                row_index=2,
                label_class=TileLabelClass.NEGATIVE_ONLY,
            ),
        ),
    )


def test_policy_identity_payload_is_explicit() -> None:
    assert sampling_policy_identity_payload(
        LOOP1_SAMPLING_POLICY
    ) == {
        "select_all_eligible": True,
        "exclude_all_ignore": True,
        "order": "catalog_order",
        "hard_negative_handling": "require_source_provenance",
    }


def test_selection_identity_payload_preserves_partition() -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    payload = tile_sampling_selection_identity_payload(
        selection,
        catalog=catalog,
    )
    assert payload["schema_version"] == (
        TILE_SAMPLING_SELECTION_SCHEMA_VERSION
    )
    assert payload["tile_catalog_id"] == build_tile_catalog_id(catalog)
    assert payload["selected_tile_ids"] == [
        catalog.tiles[0].tile_id,
        catalog.tiles[2].tile_id,
    ]
    assert payload["excluded_tile_ids"] == [
        catalog.tiles[1].tile_id,
    ]


def test_selection_identity_is_stable() -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)

    first_id = build_tile_sampling_selection_id(
        selection,
        catalog=catalog,
    )
    second_id = build_tile_sampling_selection_id(
        selection,
        catalog=catalog,
    )
    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_selection_serialization_contains_counts_and_tiles() -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)

    payload = tile_sampling_selection_to_dict(
        selection,
        catalog=catalog,
    )
    assert payload["selected_tile_count"] == 2
    assert payload["selected_positive_tile_count"] == 1
    assert payload["selected_negative_only_tile_count"] == 1
    assert payload["excluded_tile_count"] == 1
    assert [
        tile["tile_id"]
        for tile in payload["selected_tiles"]
    ] == [
        catalog.tiles[0].tile_id,
        catalog.tiles[2].tile_id,
    ]


def test_writer_creates_canonical_selection_artifact(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    output_path = tmp_path / "nested" / "selection.json"
    result = write_tile_sampling_selection_catalog(
        selection,
        catalog=catalog,
        output_path=output_path,
    )
    assert result == output_path
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(
        output_path.read_text(encoding="utf-8")
    ) == tile_sampling_selection_to_dict(
        selection,
        catalog=catalog,
    )


def test_verification_accepts_matching_selection_artifact(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    output_path = tmp_path / "selection.json"
    write_tile_sampling_selection_catalog(
        selection,
        catalog=catalog,
        output_path=output_path,
    )
    assert verify_tile_sampling_selection_artifact(
        selection,
        catalog=catalog,
        artifact_path=output_path,
    ) == ()


def test_verification_rejects_missing_selection_artifact(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)

    errors = verify_tile_sampling_selection_artifact(
        selection,
        catalog=catalog,
        artifact_path=tmp_path / "missing.json",
    )
    assert errors == (
        "selection artifact does not exist.",
    )


def test_verification_rejects_changed_selection_content(
    tmp_path: Path,
) -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    output_path = tmp_path / "selection.json"
    write_tile_sampling_selection_catalog(
        selection,
        catalog=catalog,
        output_path=output_path,
    )
    payload = json.loads(
        output_path.read_text(encoding="utf-8")
    )
    payload["selected_tile_count"] = 99
    output_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    errors = verify_tile_sampling_selection_artifact(
        selection,
        catalog=catalog,
        artifact_path=output_path,
    )
    assert errors == (
        "selection artifact content does not match expected selection.",
    )