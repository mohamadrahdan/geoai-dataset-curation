import pytest
from pathlib import Path
from affine import Affine
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    RasterArtifactMetadata,
)
from datetime import date
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneCandidate,
    ScenePreparationResult,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RemoteRasterArtifact,
    RetrievedRasterArtifact,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineImageReference,
)
from geoai_dataset_curation.image_construction.real_image_manifest import (
    REAL_IMAGE_MANIFEST_SCHEMA_VERSION,
    RealImageArtifactMetadata,
    RealImageCompositeProvenance,
    RealImageManifest,
    RealImageSceneProvenance,
    create_real_image_artifact_metadata,
    create_real_image_composite_provenance,
    create_real_image_manifest,
    RealImageGridMetadata,
    create_real_image_grid_metadata,
    RealImageExportTrace,
    create_real_image_export_trace,
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


def test_create_real_image_composite_provenance_preserves_processing_history() -> None:
    scene_1 = SceneCandidate(
        scene_id="scene-1",
        acquisition_date=date(
            2024,
            5,
            10,
        ),
        cloud_cover=4.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
            "SCL",
        ),
    )
    scene_2 = SceneCandidate(
        scene_id="scene-2",
        acquisition_date=date(
            2024,
            5,
            20,
        ),
        cloud_cover=7.0,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
            "SCL",
        ),
    )
    preparation = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=2,
        selected_count=2,
        rejected_count=0,
        selected_scenes=(
            scene_1,
            scene_2,
        ),
    )
    request = EarthEngineCompositeRequest(
        scene_ids=(
            "scene-1",
            "scene-2",
        ),
        bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=(
            EarthEngineAggregationMethod.MEDIAN
        ),
    )
    provenance = create_real_image_composite_provenance(
        scene_preparation=preparation,
        composite_request=request,
    )
    assert isinstance(
        provenance,
        RealImageCompositeProvenance,
    )
    assert provenance.scenes == (
        RealImageSceneProvenance(
            scene_id="scene-1",
            acquisition_date=date(
                2024,
                5,
                10,
            ),
            cloud_cover=4.5,
            collection=(
                "COPERNICUS/S2_SR_HARMONIZED"
            ),
        ),
        RealImageSceneProvenance(
            scene_id="scene-2",
            acquisition_date=date(
                2024,
                5,
                20,
            ),
            cloud_cover=7.0,
            collection=(
                "COPERNICUS/S2_SR_HARMONIZED"
            ),
        ),
    )

    assert provenance.bands == (
        "B2",
        "B3",
        "B4",
        "B8",
    )
    assert provenance.aggregation_method == "median"
    assert provenance.cloud_mask_band == "SCL"
    assert (
        provenance.excluded_cloud_mask_classes
        == (
            1,
            3,
            8,
            9,
            10,
            11,
        )
    )


def test_create_real_image_composite_provenance_rejects_scene_mismatch() -> None:
    scene = SceneCandidate(
        scene_id="scene-1",
        acquisition_date=date(
            2024,
            5,
            10,
        ),
        cloud_cover=4.5,
        collection="COPERNICUS/S2_SR_HARMONIZED",
        available_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
            "SCL",
        ),
    )
    preparation = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=1,
        selected_count=1,
        rejected_count=0,
        selected_scenes=(
            scene,
        ),
    )
    request = EarthEngineCompositeRequest(
        scene_ids=(
            "different-scene",
        ),
        bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=(
            EarthEngineAggregationMethod.MEDIAN
        ),
    )
    with pytest.raises(
        ValueError,
        match="must exactly match",
    ):
        create_real_image_composite_provenance(
            scene_preparation=preparation,
            composite_request=request,
        )


def test_create_real_image_grid_metadata_preserves_exact_grid() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=97,
        height=112,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=547020.0,
            d=0.0,
            e=-10.0,
            f=3374300.0,
        ),
    )

    metadata = create_real_image_grid_metadata(grid)

    assert isinstance(
        metadata,
        RealImageGridMetadata,
    )
    assert metadata.grid_id == build_raster_grid_id(grid)
    assert metadata.crs == "EPSG:32639"
    assert metadata.width == 97
    assert metadata.height == 112
    assert metadata.pixel_size_x == 10.0
    assert metadata.pixel_size_y == 10.0
    assert metadata.transform == (
        10.0,
        0.0,
        547020.0,
        0.0,
        -10.0,
        3374300.0,
    )


def test_create_real_image_grid_metadata_rejects_non_exact_grid() -> None:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=97,
        height=112,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=None,
    )
    with pytest.raises(
        ValueError,
        match="Cannot create real-image grid metadata",
    ):
        create_real_image_grid_metadata(
            grid
        )


def test_create_real_image_export_trace_preserves_export_and_retrieval_path(
    tmp_path: Path,
) -> None:
    export_request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="sentinel2-composite:median:2-scenes"
        ),
        output_name="padena_sentinel2_image",
        grid=RasterGridSpec(
            crs="EPSG:32639",
            width=97,
            height=112,
            pixel_size_x=10.0,
            pixel_size_y=10.0,
            transform=AffineTransformSpec(
                a=10.0,
                b=0.0,
                c=547020.0,
                d=0.0,
                e=-10.0,
                f=3374300.0,
            ),
        ),
        destination=(
            EarthEngineExportDestination.DRIVE
        ),
        destination_folder="padena-images",
    )

    export_task = EarthEngineExportTaskReference(task_id="task-123")

    local_path = (
        tmp_path
        / "padena_sentinel2_image.tif"
    )

    retrieved = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri=(
                "drive://padena-images/"
                "padena_sentinel2_image.tif"
            ),
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=local_path,
    )
    trace = create_real_image_export_trace(
        export_request=export_request,
        export_task=export_task,
        retrieved_artifact=retrieved,
    )

    assert isinstance(
        trace,
        RealImageExportTrace,
    )
    assert trace.task_id == "task-123"
    assert trace.destination == "drive"
    assert (
        trace.destination_folder
        == "padena-images"
    )
    assert (
        trace.remote_artifact_uri
        == (
            "drive://padena-images/"
            "padena_sentinel2_image.tif"
        )
    )
    assert trace.local_path == local_path


def test_create_real_image_export_trace_rejects_empty_task_id(
    tmp_path: Path,
) -> None:
    export_request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="image-1"
        ),
        output_name="padena_sentinel2_image",
        grid=RasterGridSpec(
            crs="EPSG:32639",
            width=97,
            height=112,
            pixel_size_x=10.0,
            pixel_size_y=10.0,
            transform=AffineTransformSpec(
                a=10.0,
                b=0.0,
                c=547020.0,
                d=0.0,
                e=-10.0,
                f=3374300.0,
            ),
        ),
        destination=(EarthEngineExportDestination.DRIVE),
        destination_folder="padena-images",
    )

    retrieved = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri=(
                "drive://padena-images/"
                "padena_sentinel2_image.tif"
            ),
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=(
            tmp_path
            / "padena_sentinel2_image.tif"
        ),
    )

    with pytest.raises(
        ValueError,
        match="task_id",
    ):
        create_real_image_export_trace(
            export_request=export_request,
            export_task=EarthEngineExportTaskReference(
                task_id=" "
            ),
            retrieved_artifact=retrieved,
        )