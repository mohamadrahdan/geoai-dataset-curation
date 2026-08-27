import pytest
from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.real_image_manifest import (
    REAL_IMAGE_MANIFEST_SCHEMA_VERSION,
    RealImageArtifactMetadata,
    RealImageManifest,
    create_real_image_artifact_metadata,
    create_real_image_manifest,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
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


def test_create_real_image_artifact_metadata_preserves_inspected_values(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "image.tif"
    artifact_path.write_bytes(
        b"real-raster-artifact"
    )
    inspected = RasterArtifactMetadata(
        path=artifact_path,
        driver="GTiff",
        crs="EPSG:32639",
        width=97,
        height=112,
        band_count=4,
        dtypes=(
            "float64",
            "float64",
            "float64",
            "float64",
        ),
        transform=Affine(
            10.0,
            0.0,
            547020.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )

    metadata = create_real_image_artifact_metadata(inspected)
    assert isinstance(metadata, RealImageArtifactMetadata)
    assert metadata.file_size_bytes == 20
    assert metadata.driver == "GTiff"
    assert metadata.width == 97
    assert metadata.height == 112
    assert metadata.band_count == 4
    assert metadata.dtypes == (
        "float64",
        "float64",
        "float64",
        "float64",
    )


def test_create_real_image_artifact_metadata_rejects_empty_artifact(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "empty.tif"
    artifact_path.touch()

    inspected = RasterArtifactMetadata(
        path=artifact_path,
        driver="GTiff",
        crs="EPSG:32639",
        width=97,
        height=112,
        band_count=4,
        dtypes=(
            "float64",
            "float64",
            "float64",
            "float64",
        ),
        transform=Affine(
            10.0,
            0.0,
            547020.0,
            0.0,
            -10.0,
            3374300.0,
        ),
    )
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        create_real_image_artifact_metadata(
            inspected
        )