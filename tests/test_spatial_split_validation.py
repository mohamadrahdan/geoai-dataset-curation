from dataclasses import replace
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split import (
    SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION,
    SpatialSplitAssignment,
    SpatialSplitCatalog,
    SpatialSplitName,
    validate_spatial_split_assignment,
    validate_spatial_split_catalog,
)
from geoai_dataset_curation.tiling import (
    TileLabelClass,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_pair(
    *,
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
            make_pair(
                pair_character="1",
                tile_character="4",
            ),
            make_pair(
                pair_character="2",
                tile_character="5",
            ),
            make_pair(
                pair_character="3",
                tile_character="6",
            ),
        ),
    )


def make_catalog() -> tuple[
    SpatialSplitCatalog,
    ImageMaskPairCatalog,
]:
    pair_catalog = make_pair_catalog()

    catalog = SpatialSplitCatalog(
        schema_version=(
            SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION
        ),
        output_name="split-v1",
        pair_catalog_id=(
            build_image_mask_pair_catalog_id(
                pair_catalog
            )
        ),
        pair_qc_report_id=sha("d"),
        visual_review_catalog_id=sha("e"),
        grouping_policy_id=sha("f"),
        assignment_policy_id=sha("0"),
        assignments=(
            SpatialSplitAssignment(
                pair_id=sha("1"),
                tile_id=sha("4"),
                spatial_group_id=sha("7"),
                split=SpatialSplitName.TRAIN,
            ),
            SpatialSplitAssignment(
                pair_id=sha("2"),
                tile_id=sha("5"),
                spatial_group_id=sha("7"),
                split=SpatialSplitName.TRAIN,
            ),
            SpatialSplitAssignment(
                pair_id=sha("3"),
                tile_id=sha("6"),
                spatial_group_id=sha("8"),
                split=SpatialSplitName.TEST,
            ),
        ),
    )

    return catalog, pair_catalog


def test_valid_spatial_split_assignment_has_no_errors(
) -> None:
    catalog, _ = make_catalog()

    assert validate_spatial_split_assignment(
        catalog.assignments[0]
    ) == ()


def test_assignment_rejects_invalid_contract_values(
) -> None:
    assignment = SpatialSplitAssignment(
        pair_id="pair",
        tile_id="tile",
        spatial_group_id="group",
        split="train",  # type: ignore[arg-type]
    )

    assert validate_spatial_split_assignment(
        assignment
    ) == (
        "pair_id must be a valid SHA-256 identity.",
        "tile_id must be a valid SHA-256 identity.",
        (
            "spatial_group_id must be a valid "
            "SHA-256 identity."
        ),
        "split must be a SpatialSplitName.",
    )


def test_valid_spatial_split_catalog_has_no_errors(
) -> None:
    catalog, pair_catalog = make_catalog()

    assert validate_spatial_split_catalog(
        catalog,
        pair_catalog=pair_catalog,
    ) == ()


def test_catalog_rejects_invalid_metadata(
) -> None:
    catalog, pair_catalog = make_catalog()

    invalid = replace(
        catalog,
        schema_version="unsupported",
        output_name=" ",
        pair_catalog_id=sha("9"),
        pair_qc_report_id="qc",
        visual_review_catalog_id="review",
        grouping_policy_id="grouping",
        assignment_policy_id="assignment",
    )

    assert validate_spatial_split_catalog(
        invalid,
        pair_catalog=pair_catalog,
    ) == (
        "schema_version is not supported.",
        "output_name must not be empty.",
        (
            "pair_catalog_id must match "
            "the pair catalog."
        ),
        (
            "pair_qc_report_id must be a valid "
            "SHA-256 identity."
        ),
        (
            "visual_review_catalog_id must be a "
            "valid SHA-256 identity."
        ),
        (
            "grouping_policy_id must be a valid "
            "SHA-256 identity."
        ),
        (
            "assignment_policy_id must be a valid "
            "SHA-256 identity."
        ),
    )


def test_catalog_requires_non_empty_assignments(
) -> None:
    catalog, pair_catalog = make_catalog()

    errors = validate_spatial_split_catalog(
        replace(
            catalog,
            assignments=(),
        ),
        pair_catalog=pair_catalog,
    )

    assert (
        "assignments must not be empty."
        in errors
    )
    assert (
        "assignments must cover every pair "
        "in catalog order."
        in errors
    )


def test_catalog_rejects_non_tuple_assignments(
) -> None:
    catalog, pair_catalog = make_catalog()

    invalid = replace(
        catalog,
        assignments=list(
            catalog.assignments
        ),  # type: ignore[arg-type]
    )

    assert validate_spatial_split_catalog(
        invalid,
        pair_catalog=pair_catalog,
    ) == (
        "assignments must be a tuple.",
    )


def test_catalog_rejects_duplicate_pair_and_tile_ids(
) -> None:
    catalog, pair_catalog = make_catalog()

    duplicate = replace(
        catalog,
        assignments=(
            catalog.assignments[0],
            catalog.assignments[0],
            catalog.assignments[2],
        ),
    )

    errors = validate_spatial_split_catalog(
        duplicate,
        pair_catalog=pair_catalog,
    )

    assert (
        "assignment pair_id values must be unique."
        in errors
    )
    assert (
        "assignment tile_id values must be unique."
        in errors
    )


def test_catalog_requires_complete_catalog_order(
) -> None:
    catalog, pair_catalog = make_catalog()

    reordered = replace(
        catalog,
        assignments=tuple(
            reversed(catalog.assignments)
        ),
    )

    errors = validate_spatial_split_catalog(
        reordered,
        pair_catalog=pair_catalog,
    )

    assert (
        "assignments must cover every pair "
        "in catalog order."
        in errors
    )


def test_catalog_rejects_pair_tile_mismatch(
) -> None:
    catalog, pair_catalog = make_catalog()

    mismatched_assignment = replace(
        catalog.assignments[0],
        tile_id=sha("9"),
    )

    invalid = replace(
        catalog,
        assignments=(
            mismatched_assignment,
            *catalog.assignments[1:],
        ),
    )

    errors = validate_spatial_split_catalog(
        invalid,
        pair_catalog=pair_catalog,
    )

    assert (
        "assignments[0].tile_id must match "
        "the assigned pair."
        in errors
    )


def test_catalog_rejects_group_across_splits(
) -> None:
    catalog, pair_catalog = make_catalog()

    conflicting_assignment = replace(
        catalog.assignments[1],
        split=SpatialSplitName.VALIDATION,
    )

    invalid = replace(
        catalog,
        assignments=(
            catalog.assignments[0],
            conflicting_assignment,
            catalog.assignments[2],
        ),
    )

    errors = validate_spatial_split_catalog(
        invalid,
        pair_catalog=pair_catalog,
    )

    assert (
        "each spatial_group_id must belong "
        "to exactly one split."
        in errors
    )