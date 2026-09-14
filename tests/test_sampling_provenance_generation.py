from dataclasses import replace
import numpy as np
import pytest
from geoai_dataset_curation.sampling import (
    NegativeProvenanceKind,
    build_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    negative_pixel_count: int,
) -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 2,
        column_offset_pixels=0,
        read_width_pixels=2,
        read_height_pixels=2,
        output_width_pixels=2,
        output_height_pixels=2,
        left=0.0,
        bottom=float(row_index * 20),
        right=20.0,
        top=float((row_index + 1) * 20),
        positive_pixel_count=0,
        negative_pixel_count=negative_pixel_count,
        ignore_pixel_count=4 - negative_pixel_count,
    )


def make_catalog() -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="provenance-generation-candidates",
        image_artifact_path="artifacts/image.tif",
        label_artifact_path="artifacts/labels.tif",
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(
            make_candidate(
                digest_character="c",
                row_index=0,
                negative_pixel_count=2,
            ),
            make_candidate(
                digest_character="d",
                row_index=1,
                negative_pixel_count=3,
            ),
            make_candidate(
                digest_character="e",
                row_index=2,
                negative_pixel_count=0,
            ),
        ),
    )


def make_masks() -> tuple[np.ndarray, np.ndarray]:
    ordinary = np.zeros(
        (6, 2),
        dtype=bool,
    )
    hard = np.zeros(
        (6, 2),
        dtype=bool,
    )

    ordinary[0, 0] = True
    ordinary[0, 1] = True
    ordinary[2, 0] = True
    ordinary[2, 1] = True
    hard[2, 1] = True
    hard[3, 0] = True

    return ordinary, hard


def build_provenance():
    catalog = make_catalog()
    ordinary, hard = make_masks()
    return build_tile_negative_provenance_catalog(
        catalog,
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        ordinary_negative_mask=ordinary,
        hard_negative_mask=hard,
    )


def test_builder_computes_source_specific_counts() -> None:
    provenance = build_provenance()

    assert tuple(
        (
            record.ordinary_negative_pixel_count,
            record.hard_negative_pixel_count,
            record.shared_negative_pixel_count,
            record.union_negative_pixel_count,
            record.kind,
        )
        for record in provenance.records
    ) == (
        (
            2,
            0,
            0,
            2,
            NegativeProvenanceKind.ORDINARY_NEGATIVE,
        ),
        (
            2,
            2,
            1,
            3,
            NegativeProvenanceKind.MIXED_NEGATIVE,
        ),
        (
            0,
            0,
            0,
            0,
            NegativeProvenanceKind.NONE,
        ),
    )


def test_builder_links_source_and_catalog_identities() -> None:
    catalog = make_catalog()
    provenance = build_provenance()
    assert (provenance.tile_catalog_id == build_tile_catalog_id(catalog))
    assert (provenance.ordinary_negative_source_id == "ordinary-negative")
    assert (provenance.hard_negative_source_id == "hard-negative")
    assert provenance.hard_negative_tile_count == 1


def test_builder_preserves_catalog_order() -> None:
    catalog = make_catalog()
    provenance = build_provenance()
    assert tuple(
        record.tile_id
        for record in provenance.records
    ) == tuple(
        candidate.tile_id
        for candidate in catalog.tiles
    )


def test_repeated_build_is_deterministic() -> None:
    assert build_provenance() == build_provenance()


def test_builder_rejects_non_boolean_mask() -> None:
    catalog = make_catalog()
    ordinary, hard = make_masks()
    with pytest.raises(
        ValueError,
        match=("ordinary_negative_mask must have boolean dtype"),
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="ordinary-negative",
            hard_negative_source_id="hard-negative",
            ordinary_negative_mask=ordinary.astype(
                np.uint8
            ),
            hard_negative_mask=hard,
        )


def test_builder_rejects_wrong_mask_shape() -> None:
    catalog = make_catalog()
    ordinary, hard = make_masks()
    with pytest.raises(
        ValueError,
        match=(
            "negative source masks must match the "
            "candidate catalog raster extent"
        ),
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="ordinary-negative",
            hard_negative_source_id="hard-negative",
            ordinary_negative_mask=ordinary[:4, :],
            hard_negative_mask=hard[:4, :],
        )


def test_builder_rejects_unexplained_negative_pixels() -> None:
    catalog = make_catalog()
    ordinary, hard = make_masks()
    ordinary[0, 1] = False
    with pytest.raises(
        ValueError,
        match="source-derived negative union must match",
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="ordinary-negative",
            hard_negative_source_id="hard-negative",
            ordinary_negative_mask=ordinary,
            hard_negative_mask=hard,
        )


def test_builder_rejects_negative_evidence_in_all_ignore_tile() -> None:
    catalog = make_catalog()
    ordinary, hard = make_masks()
    hard[4, 0] = True
    with pytest.raises(
        ValueError,
        match="source-derived negative union must match",
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="ordinary-negative",
            hard_negative_source_id="hard-negative",
            ordinary_negative_mask=ordinary,
            hard_negative_mask=hard,
        )


def test_builder_rejects_identical_source_ids() -> None:
    catalog = make_catalog()
    ordinary, hard = make_masks()

    with pytest.raises(
        ValueError,
        match=("ordinary and hard-negative source IDs must differ"),
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="negative-source",
            hard_negative_source_id="negative-source",
            ordinary_negative_mask=ordinary,
            hard_negative_mask=hard,
        )


def test_builder_rejects_invalid_catalog() -> None:
    catalog = replace(
        make_catalog(),
        tiles=(),
    )
    ordinary, hard = make_masks()
    with pytest.raises(
        ValueError,
        match=(
            "Cannot build provenance from an invalid "
            "tile catalog"
        ),
    ):
        build_tile_negative_provenance_catalog(
            catalog,
            ordinary_negative_source_id="ordinary-negative",
            hard_negative_source_id="hard-negative",
            ordinary_negative_mask=ordinary,
            hard_negative_mask=hard,
        )