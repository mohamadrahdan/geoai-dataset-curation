from geoai_dataset_curation.spatial_split import (
    SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION,
    SpatialSplitAssignment,
    SpatialSplitCatalog,
    SpatialSplitName,
)


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def test_spatial_split_names_are_stable() -> None:
    assert SpatialSplitName.TRAIN.value == "train"
    assert (
        SpatialSplitName.VALIDATION.value
        == "validation"
    )
    assert SpatialSplitName.TEST.value == "test"


def test_spatial_split_catalog_reports_derived_counts(
) -> None:
    catalog = SpatialSplitCatalog(
        schema_version=(
            SPATIAL_SPLIT_CATALOG_SCHEMA_VERSION
        ),
        output_name="split-v1",
        pair_catalog_id=sha("a"),
        pair_qc_report_id=sha("b"),
        visual_review_catalog_id=sha("c"),
        grouping_policy_id=sha("d"),
        assignment_policy_id=sha("e"),
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
    assert catalog.assignment_count == 3
    assert catalog.spatial_group_count == 2
    assert catalog.train_count == 2
    assert catalog.validation_count == 0
    assert catalog.test_count == 1