from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.label_rasterization import (
    HARD_NEGATIVE_REFERENCE_PATH_ENV,
    NEGATIVE_REFERENCE_PATH_ENV,
    POSITIVE_REFERENCE_PATH_ENV,
    load_real_reference_source_configs,
)


def test_real_reference_configs_load_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        POSITIVE_REFERENCE_PATH_ENV,
        "private/positive.shp",
    )
    monkeypatch.setenv(
        NEGATIVE_REFERENCE_PATH_ENV,
        "private/negative.shp",
    )
    monkeypatch.setenv(
        HARD_NEGATIVE_REFERENCE_PATH_ENV,
        "private/hard-negative.shp",
    )
    configs = load_real_reference_source_configs(
        positive_source_id="positive-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    assert len(configs) == 3
    assert (
        configs[0].supervision
        == SupervisionKind.POSITIVE_REFERENCE
    )
    assert (
        configs[1].supervision
        == SupervisionKind.NEGATIVE_REFERENCE
    )
    assert (
        configs[2].supervision
        == SupervisionKind.HARD_NEGATIVE_REFERENCE
    )


def test_missing_real_reference_path_is_rejected(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        POSITIVE_REFERENCE_PATH_ENV,
        raising=False,
    )
    monkeypatch.setenv(
        NEGATIVE_REFERENCE_PATH_ENV,
        "private/negative.shp",
    )
    monkeypatch.setenv(
        HARD_NEGATIVE_REFERENCE_PATH_ENV,
        "private/hard-negative.shp",
    )
    try:
        load_real_reference_source_configs(
            positive_source_id="positive-reference",
            negative_source_id="negative-reference",
            hard_negative_source_id="hard-negative-reference",
        )
    except ValueError as error:
        assert POSITIVE_REFERENCE_PATH_ENV in str(error)
    else:
        raise AssertionError(
            "Missing positive reference path was not rejected."
        )