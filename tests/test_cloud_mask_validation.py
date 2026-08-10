from geoai_dataset_curation.image_construction import (
    Sentinel2CloudMaskSpec,
    validate_sentinel2_cloud_mask_spec,
)


def test_cloud_mask_validation_accepts_default_policy() -> None:
    spec = Sentinel2CloudMaskSpec()
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert errors == ()


def test_cloud_mask_validation_accepts_custom_policy() -> None:
    spec = Sentinel2CloudMaskSpec(
        excluded_scl_classes=(3, 8, 9),
    )
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert errors == ()


def test_cloud_mask_validation_rejects_empty_scl_band() -> None:
    spec = Sentinel2CloudMaskSpec(
        scl_band=" ",
    )
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert (
        "cloud_mask.scl_band must not be empty."
        in errors
    )


def test_cloud_mask_validation_rejects_empty_class_set() -> None:
    spec = Sentinel2CloudMaskSpec(
        excluded_scl_classes=(),
    )
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert (
        "cloud_mask.excluded_scl_classes must contain "
        "at least one class."
        in errors
    )


def test_cloud_mask_validation_rejects_duplicate_classes() -> None:
    spec = Sentinel2CloudMaskSpec(
        excluded_scl_classes=(3, 8, 8, 9),
    )
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert (
        "cloud_mask.excluded_scl_classes must not "
        "contain duplicates."
        in errors
    )


def test_cloud_mask_validation_rejects_out_of_range_classes() -> None:
    spec = Sentinel2CloudMaskSpec(
        excluded_scl_classes=(-1, 3, 12),
    )
    errors = validate_sentinel2_cloud_mask_spec(spec)
    assert (
        "cloud_mask.excluded_scl_classes must contain "
        "values between 0 and 11."
        in errors
    )