from dataclasses import FrozenInstanceError
import pytest
from geoai_dataset_curation.image_construction import (
    DEFAULT_SENTINEL2_EXCLUDED_SCL_CLASSES,
    SENTINEL2_SCL_BAND,
    Sentinel2CloudMaskSpec,
)


def test_default_cloud_mask_spec_uses_scl_band() -> None:
    spec = Sentinel2CloudMaskSpec()
    assert spec.scl_band == "SCL"
    assert spec.scl_band == SENTINEL2_SCL_BAND


def test_default_cloud_mask_spec_excludes_expected_scl_classes() -> None:
    spec = Sentinel2CloudMaskSpec()
    assert spec.excluded_scl_classes == (
        1,
        3,
        8,
        9,
        10,
        11,
    )
    assert (
        spec.excluded_scl_classes
        == DEFAULT_SENTINEL2_EXCLUDED_SCL_CLASSES
    )


def test_cloud_mask_spec_accepts_custom_policy() -> None:
    spec = Sentinel2CloudMaskSpec(
        scl_band="CUSTOM_SCL",
        excluded_scl_classes=(3, 8, 9),
    )
    assert spec.scl_band == "CUSTOM_SCL"
    assert spec.excluded_scl_classes == (
        3,
        8,
        9,
    )


def test_cloud_mask_spec_is_immutable() -> None:
    spec = Sentinel2CloudMaskSpec()
    with pytest.raises(FrozenInstanceError):
        setattr(
            spec,
            "excluded_scl_classes",
            (3, 9),
        )