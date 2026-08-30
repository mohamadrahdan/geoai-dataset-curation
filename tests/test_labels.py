import pytest
from geoai_dataset_curation.contracts import (
    LOOP1_LABEL_SCHEMA,
    LabelValue,
    SupervisionKind,
    get_label_schema_entry,
)


def test_label_values_match_training_contract() -> None:
    assert LabelValue.NEGATIVE == 0
    assert LabelValue.POSITIVE == 1
    assert LabelValue.IGNORE == 255


def test_loop1_schema_contains_all_supervision_kinds() -> None:
    assert {
        entry.supervision
        for entry in LOOP1_LABEL_SCHEMA
    } == set(SupervisionKind)


@pytest.mark.parametrize(
    ("supervision", "target", "contributes_to_loss"),
    [(
            SupervisionKind.POSITIVE_REFERENCE,
            LabelValue.POSITIVE,
            True,
        ),
        (
            SupervisionKind.NEGATIVE_REFERENCE,
            LabelValue.NEGATIVE,
            True,
        ),
        (
            SupervisionKind.HARD_NEGATIVE_REFERENCE,
            LabelValue.NEGATIVE,
            True,
        ),
        (
            SupervisionKind.UNLABELED,
            LabelValue.IGNORE,
            False,
        ),
        (
            SupervisionKind.NODATA,
            LabelValue.IGNORE,
            False,
        ),
    ],
)
def test_supervision_maps_to_expected_training_target(
    supervision: SupervisionKind,
    target: LabelValue,
    contributes_to_loss: bool,
) -> None:
    entry = get_label_schema_entry(supervision)
    assert entry.target == target
    assert entry.contributes_to_loss is contributes_to_loss


def test_hard_negative_remains_distinct_from_regular_negative() -> None:
    regular = get_label_schema_entry(SupervisionKind.NEGATIVE_REFERENCE)
    hard = get_label_schema_entry(SupervisionKind.HARD_NEGATIVE_REFERENCE)
    assert regular.supervision != hard.supervision
    assert regular.target == hard.target == LabelValue.NEGATIVE


def test_unlabeled_pixels_are_not_negative_training_targets() -> None:
    entry = get_label_schema_entry(SupervisionKind.UNLABELED)
    assert entry.target == LabelValue.IGNORE
    assert entry.target != LabelValue.NEGATIVE
    assert entry.contributes_to_loss is False


def test_nodata_and_unlabeled_share_ignore_target_but_not_semantics() -> None:
    unlabeled = get_label_schema_entry(SupervisionKind.UNLABELED)
    nodata = get_label_schema_entry(SupervisionKind.NODATA)
    assert unlabeled.supervision != nodata.supervision
    assert unlabeled.target == nodata.target == LabelValue.IGNORE