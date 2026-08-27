import pytest
from geoai_dataset_curation.image_construction.real_image_manifest import (
    REAL_IMAGE_MANIFEST_SCHEMA_VERSION,
    RealImageManifest,
    create_real_image_manifest,
)


def test_create_real_image_manifest_preserves_identity() -> None:
    manifest = create_real_image_manifest(
        source_id="padena_aoi",
        output_name="padena_sentinel2_image",
        artifact_uri=(
            "drive://padena-images/"
            "padena_sentinel2_image.tif"
        ),
    )
    assert isinstance(
        manifest,
        RealImageManifest,
    )
    assert (
        manifest.schema_version
        == REAL_IMAGE_MANIFEST_SCHEMA_VERSION
    )
    assert manifest.source_id == "padena_aoi"
    assert (
        manifest.output_name
        == "padena_sentinel2_image"
    )
    assert manifest.has_artifact is True


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("source_id", " "),
        ("output_name", ""),
        ("artifact_uri", " "),
    ],
)
def test_create_real_image_manifest_rejects_empty_identity_fields(
    field_name: str,
    field_value: str,
) -> None:
    values = {
        "source_id": "padena_aoi",
        "output_name": "padena_sentinel2_image",
        "artifact_uri": (
            "drive://padena-images/"
            "padena_sentinel2_image.tif"
        ),
    }

    values[field_name] = field_value
    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        create_real_image_manifest(
            **values,
        )