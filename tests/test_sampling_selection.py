from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    TileSamplingSelection,
    select_tile_candidates,
    validate_tile_sampling_selection,
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
            make_candidate(
                digest_character="f",
                row_index=3,
                label_class=TileLabelClass.ALL_IGNORE,
            ),
        ),
    )


def test_selection_includes_every_supervised_candidate() -> None:
    catalog = make_catalog()

    selection = select_tile_candidates(catalog)

    assert tuple(
        candidate.label_class
        for candidate in selection.selected_candidates
    ) == (
        TileLabelClass.POSITIVE,
        TileLabelClass.NEGATIVE_ONLY,
    )
    assert selection.selected_tile_count == 2
    assert selection.selected_positive_tile_count == 1
    assert selection.selected_negative_only_tile_count == 1


def test_selection_excludes_all_ignore_without_relabeling() -> None:
    catalog = make_catalog()

    selection = select_tile_candidates(catalog)

    assert selection.excluded_tile_ids == (
        catalog.tiles[1].tile_id,
        catalog.tiles[3].tile_id,
    )
    assert selection.excluded_tile_count == 2


def test_selection_preserves_catalog_order() -> None:
    catalog = make_catalog()

    selection = select_tile_candidates(catalog)

    assert tuple(
        candidate.tile_id
        for candidate in selection.selected_candidates
    ) == (
        catalog.tiles[0].tile_id,
        catalog.tiles[2].tile_id,
    )


def test_selection_preserves_catalog_identity() -> None:
    catalog = make_catalog()

    selection = select_tile_candidates(catalog)

    assert selection.catalog_id == build_tile_catalog_id(catalog)
    assert validate_tile_sampling_selection(
        selection,
        catalog=catalog,
    ) == ()


def test_repeated_selection_is_deterministic() -> None:
    catalog = make_catalog()

    assert select_tile_candidates(
        catalog
    ) == select_tile_candidates(catalog)


def test_selection_rejects_invalid_catalog() -> None:
    catalog = replace(
        make_catalog(),
        tiles=(),
    )

    with pytest.raises(
        ValueError,
        match="Cannot sample an invalid tile catalog",
    ):
        select_tile_candidates(catalog)


def test_validation_rejects_wrong_catalog_identity() -> None:
    catalog = make_catalog()
    selection = replace(
        select_tile_candidates(catalog),
        catalog_id="sha256:" + ("0" * 64),
    )

    errors = validate_tile_sampling_selection(
        selection,
        catalog=catalog,
    )

    assert (
        "catalog_id must match the candidate catalog."
        in errors
    )


def test_validation_rejects_incomplete_partition() -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    incomplete = TileSamplingSelection(
        catalog_id=selection.catalog_id,
        selected_candidates=selection.selected_candidates,
        excluded_tile_ids=selection.excluded_tile_ids[:-1],
    )

    errors = validate_tile_sampling_selection(
        incomplete,
        catalog=catalog,
    )

    assert (
        "selected and excluded tile IDs must "
        "partition the catalog."
        in errors
    )


def test_validation_rejects_all_ignore_as_selected() -> None:
    catalog = make_catalog()
    selection = select_tile_candidates(catalog)
    invalid = replace(
        selection,
        selected_candidates=(
            *selection.selected_candidates,
            catalog.tiles[1],
        ),
        excluded_tile_ids=(
            catalog.tiles[3].tile_id,
        ),
    )

    errors = validate_tile_sampling_selection(
        invalid,
        catalog=catalog,
    )

    assert (
        "selected_candidates must contain every supervised "
        "tile in catalog order."
        in errors
    )