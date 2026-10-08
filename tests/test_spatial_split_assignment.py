from dataclasses import replace
import pytest
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
)
from geoai_dataset_curation.spatial_split import (
    SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
    SpatialAssignmentPolicy,
    SpatialLeakageGroup,
    SpatialLeakageGroupCatalog,
    SpatialSplitInputAcceptance,
    SpatialSplitName,
    build_spatial_assignment_policy_id,
    build_spatial_leakage_group_id,
    build_spatial_split_catalog,
    validate_spatial_assignment_policy,
    validate_spatial_split_catalog,
)
from geoai_dataset_curation.tiling import TileLabelClass


def sha(character: str) -> str:
    return "sha256:" + (character * 64)


def make_policy(seed: int = 42) -> SpatialAssignmentPolicy:
    return SpatialAssignmentPolicy(
        train_fraction=0.6,
        validation_fraction=0.2,
        test_fraction=0.2,
        seed=seed,
    )


def make_pair(
    pair_character: str,
    tile_character: str,
    label_class: TileLabelClass,
) -> ImageMaskPairRecord:
    provenance = NegativeProvenanceKind.NONE
    if label_class == TileLabelClass.NEGATIVE_ONLY:
        provenance = NegativeProvenanceKind.ORDINARY_NEGATIVE

    return ImageMaskPairRecord(
        pair_id=sha(pair_character),
        tile_id=sha(tile_character),
        image_tile_path=f"images/{pair_character}.tif",
        mask_tile_path=f"masks/{pair_character}.tif",
        label_class=label_class,
        negative_provenance_kind=provenance,
    )


def make_pair_catalog() -> ImageMaskPairCatalog:
    return ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="pairs-v1",
        tile_catalog_id=sha("a"),
        selection_id=sha("b"),
        provenance_catalog_id=sha("c"),
        source_image_artifact_path="image.tif",
        source_label_artifact_path="label.tif",
        pairs=(
            make_pair("1", "7", TileLabelClass.POSITIVE),
            make_pair("2", "8", TileLabelClass.POSITIVE),
            make_pair("3", "9", TileLabelClass.NEGATIVE_ONLY),
            make_pair("4", "a", TileLabelClass.NEGATIVE_ONLY),
            make_pair("5", "b", TileLabelClass.NEGATIVE_ONLY),
            make_pair("6", "c", TileLabelClass.NEGATIVE_ONLY),
        ),
    )


def make_group(
    *,
    pair_ids: tuple[str, ...],
    tile_ids: tuple[str, ...],
) -> SpatialLeakageGroup:
    return SpatialLeakageGroup(
        spatial_group_id=build_spatial_leakage_group_id(
            pair_ids=pair_ids,
            tile_ids=tile_ids,
        ),
        pair_ids=pair_ids,
        tile_ids=tile_ids,
    )


def make_group_catalog(
    pair_catalog: ImageMaskPairCatalog,
) -> SpatialLeakageGroupCatalog:
    return SpatialLeakageGroupCatalog(
        schema_version=SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION,
        output_name="groups-v1",
        pair_catalog_id=build_image_mask_pair_catalog_id(pair_catalog),
        relationship_catalog_id=sha("d"),
        grouping_policy_id=sha("e"),
        groups=(
            make_group(
                pair_ids=(sha("1"), sha("3")),
                tile_ids=(sha("7"), sha("9")),
            ),
            make_group(
                pair_ids=(sha("2"),),
                tile_ids=(sha("8"),),
            ),
            make_group(
                pair_ids=(sha("4"), sha("5")),
                tile_ids=(sha("a"), sha("b")),
            ),
            make_group(
                pair_ids=(sha("6"),),
                tile_ids=(sha("c"),),
            ),
        ),
    )


def make_acceptance(
    pair_catalog: ImageMaskPairCatalog,
) -> SpatialSplitInputAcceptance:
    return SpatialSplitInputAcceptance(
        pair_catalog_id=build_image_mask_pair_catalog_id(pair_catalog),
        pair_qc_report_id=sha("f"),
        visual_review_catalog_id=sha("0"),
        pair_ids=tuple(pair.pair_id for pair in pair_catalog.pairs),
        tile_ids=tuple(pair.tile_id for pair in pair_catalog.pairs),
    )


def make_context() -> tuple[
    SpatialSplitInputAcceptance,
    ImageMaskPairCatalog,
    SpatialLeakageGroupCatalog,
]:
    pair_catalog = make_pair_catalog()
    return (
        make_acceptance(pair_catalog),
        pair_catalog,
        make_group_catalog(pair_catalog),
    )


def test_valid_assignment_policy_has_no_errors() -> None:
    assert validate_spatial_assignment_policy(make_policy()) == ()


def test_assignment_policy_rejects_invalid_values() -> None:
    invalid_policy = SpatialAssignmentPolicy(
        train_fraction=0.7,
        validation_fraction=0.2,
        test_fraction=0.2,
        seed=True,
    )

    assert validate_spatial_assignment_policy(invalid_policy) == (
        "split fractions must sum to one.",
        "seed must be a non-negative integer.",
    )


def test_assignment_policy_identity_is_stable_and_semantic() -> None:
    policy = make_policy()
    assert build_spatial_assignment_policy_id(policy) == (
        build_spatial_assignment_policy_id(policy)
    )
    assert build_spatial_assignment_policy_id(policy) != (
        build_spatial_assignment_policy_id(make_policy(seed=43))
    )


def test_assignment_is_deterministic_and_covers_every_pair() -> None:
    acceptance, pair_catalog, group_catalog = make_context()

    first = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=make_policy(),
        output_name="split-v1",
    )
    second = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=make_policy(),
        output_name="split-v1",
    )
    assert first == second
    assert first.assignment_count == pair_catalog.pair_count
    assert tuple(assignment.pair_id for assignment in first.assignments) == (
        tuple(pair.pair_id for pair in pair_catalog.pairs)
    )
    assert validate_spatial_split_catalog(
        first,
        pair_catalog=pair_catalog,
    ) == ()


def test_every_spatial_group_stays_in_one_split() -> None:
    acceptance, pair_catalog, group_catalog = make_context()

    catalog = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=make_policy(),
        output_name="split-v1",
    )

    splits_by_group: dict[str, set[SpatialSplitName]] = {}
    for assignment in catalog.assignments:
        splits_by_group.setdefault(
            assignment.spatial_group_id,
            set(),
        ).add(assignment.split)

    assert all(
        len(splits) == 1
        for splits in splits_by_group.values()
    )


def test_all_requested_splits_receive_at_least_one_group() -> None:
    acceptance, pair_catalog, group_catalog = make_context()

    catalog = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=make_policy(),
        output_name="split-v1",
    )
    assert catalog.train_count > 0
    assert catalog.validation_count > 0
    assert catalog.test_count > 0


def test_assignment_keeps_exact_qc_and_policy_evidence() -> None:
    acceptance, pair_catalog, group_catalog = make_context()

    catalog = build_spatial_split_catalog(
        acceptance,
        pair_catalog=pair_catalog,
        group_catalog=group_catalog,
        policy=make_policy(),
        output_name="split-v1",
    )
    assert catalog.pair_qc_report_id == acceptance.pair_qc_report_id
    assert (
        catalog.visual_review_catalog_id
        == acceptance.visual_review_catalog_id
    )
    assert catalog.grouping_policy_id == group_catalog.grouping_policy_id
    assert catalog.assignment_policy_id == (
        build_spatial_assignment_policy_id(make_policy())
    )


def test_invalid_group_population_is_rejected() -> None:
    acceptance, pair_catalog, group_catalog = make_context()
    incomplete_group_catalog = replace(
        group_catalog,
        groups=group_catalog.groups[:-1],
    )

    with pytest.raises(
        ValueError,
        match="groups must cover every pair exactly once",
    ):
        build_spatial_split_catalog(
            acceptance,
            pair_catalog=pair_catalog,
            group_catalog=incomplete_group_catalog,
            policy=make_policy(),
            output_name="split-v1",
        )


def test_fewer_than_three_groups_are_rejected() -> None:
    acceptance, pair_catalog, group_catalog = make_context()
    changed_group_catalog = replace(
        group_catalog,
        groups=group_catalog.groups[:2],
    )

    with pytest.raises(
        ValueError,
        match="at least three spatial groups are required",
    ):
        build_spatial_split_catalog(
            acceptance,
            pair_catalog=pair_catalog,
            group_catalog=changed_group_catalog,
            policy=make_policy(),
            output_name="split-v1",
        )