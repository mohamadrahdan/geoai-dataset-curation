"Validation rules for Sentinel-2 cloud-mask policies"
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)


MIN_SENTINEL2_SCL_CLASS = 0
MAX_SENTINEL2_SCL_CLASS = 11
def validate_sentinel2_cloud_mask_spec(
    spec: Sentinel2CloudMaskSpec,
) -> tuple[str, ...]:
    "Return validation errors for one Sentinel-2 cloud-mask policy"
    errors: list[str] = []
    if not spec.scl_band.strip():
        errors.append(
            "cloud_mask.scl_band must not be empty."
        )

    if not spec.excluded_scl_classes:
        errors.append(
            "cloud_mask.excluded_scl_classes must contain "
            "at least one class."
        )

    if (
        len(set(spec.excluded_scl_classes))
        != len(spec.excluded_scl_classes)
    ):
        errors.append(
            "cloud_mask.excluded_scl_classes must not "
            "contain duplicates."
        )

    if any(
        class_value < MIN_SENTINEL2_SCL_CLASS
        or class_value > MAX_SENTINEL2_SCL_CLASS
        for class_value in spec.excluded_scl_classes
    ):
        errors.append(
            "cloud_mask.excluded_scl_classes must contain "
            "values between 0 and 11."
        )

    return tuple(errors)