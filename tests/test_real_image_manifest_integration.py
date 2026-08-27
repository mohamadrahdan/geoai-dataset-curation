from datetime import date
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
import pytest
from geoai_dataset_curation.image_construction.artifact_retrieval import (
    RasterArtifactFormat,
    RemoteRasterArtifact,
    RetrievedRasterArtifact,
)
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineImageReference,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)
from geoai_dataset_curation.image_construction.real_image_manifest import (
    REAL_IMAGE_MANIFEST_SCHEMA_VERSION,
    create_complete_real_image_manifest,
    real_image_manifest_to_dict,
)
from geoai_dataset_curation.scene_preparation.contracts import (
    SceneCandidate,
    ScenePreparationResult,
)


def test_complete_real_image_manifest_integrates_real_raster_metadata(
    tmp_path: Path,
) -> None:
    raster_path = (
        tmp_path
        / "padena_sentinel2_image.tif"
    )

    transform = Affine(
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    )

    data = np.zeros(
        (4, 8, 16),
        dtype="uint16",
    )

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        width=16,
        height=8,
        count=4,
        dtype="uint16",
        crs="EPSG:32639",
        transform=transform,
    ) as dataset:
        dataset.write(data)

    inspected = inspect_raster_artifact(raster_path)

    scene = SceneCandidate(
        scene_id="S2_SCENE_001",
        acquisition_date=date(
            2024,
            5,
            18,
        ),
        cloud_cover=8.5,
        collection=("COPERNICUS/S2_SR_HARMONIZED"),
        available_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
            "SCL",
        ),
    )

    scene_preparation = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=1,
        selected_count=1,
        rejected_count=0,
        selected_scenes=(scene,),
    )

    composite_request = EarthEngineCompositeRequest(
        scene_ids=("S2_SCENE_001",),
        bands=(
            "B2",
            "B3",
            "B4",
            "B8",
        ),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=(EarthEngineAggregationMethod.MEDIAN),
    )

    approved_grid = RasterGridSpec(
        crs="EPSG:32639",
        width=16,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        ),
    )

    remote = RemoteRasterArtifact(
        uri=(
            "drive://padena-images/"
            "padena_sentinel2_image.tif"
        ),
        format=RasterArtifactFormat.GEOTIFF,
    )

    retrieved = RetrievedRasterArtifact(
        source=remote,
        local_path=raster_path,
    )

    export_request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:padena"
        ),
        output_name="padena_sentinel2_image",
        grid=approved_grid,
        destination=(EarthEngineExportDestination.DRIVE),
        destination_folder="padena-images",
    )

    export_task = EarthEngineExportTaskReference(task_id="task-123")

    manifest = create_complete_real_image_manifest(
        scene_preparation=scene_preparation,
        composite_request=composite_request,
        export_request=export_request,
        export_task=export_task,
        retrieved_artifact=retrieved,
        inspected_metadata=inspected,
        approved_grid=approved_grid,
    )

    payload = real_image_manifest_to_dict(manifest)

    assert (
        payload["schema_version"]
        == REAL_IMAGE_MANIFEST_SCHEMA_VERSION
    )
    assert payload["source_id"] == "padena_aoi"
    assert payload["artifact"]["driver"] == "GTiff"
    assert payload["artifact"]["width"] == 16
    assert payload["artifact"]["height"] == 8
    assert payload["artifact"]["band_count"] == 4
    assert payload["provenance"]["scenes"][0]["scene_id"] == "S2_SCENE_001"
    assert payload["provenance"]["aggregation_method"] == "median"
    assert payload["grid"]["transform"] == [
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    ]
    assert payload["export_trace"]["remote_artifact_uri"] == remote.uri


def test_complete_real_image_manifest_rejects_different_inspected_path(
    tmp_path: Path,
) -> None:
    retrieved_path = (
        tmp_path
        / "retrieved.tif"
    )
    inspected_path = (
        tmp_path
        / "different.tif"
    )

    data = np.zeros(
        (4, 8, 16),
        dtype="uint16",
    )

    transform = Affine(
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    )

    with rasterio.open(
        inspected_path,
        "w",
        driver="GTiff",
        width=16,
        height=8,
        count=4,
        dtype="uint16",
        crs="EPSG:32639",
        transform=transform,
    ) as dataset:
        dataset.write(data)

    inspected = inspect_raster_artifact(
        inspected_path
    )

    scene = SceneCandidate(
        scene_id="S2_SCENE_001",
        acquisition_date=date(
            2024,
            5,
            18,
        ),
        cloud_cover=8.5,
        collection=(
            "COPERNICUS/S2_SR_HARMONIZED"
        ),
        available_bands=(
            "B2",
            "B3",
            "B4",
            "B8",
            "SCL",
        ),
    )

    scene_preparation = ScenePreparationResult(
        source_id="padena_aoi",
        candidate_count=1,
        selected_count=1,
        rejected_count=0,
        selected_scenes=(scene,),
    )

    composite_request = EarthEngineCompositeRequest(
        scene_ids=("S2_SCENE_001",),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=(
            EarthEngineAggregationMethod.MEDIAN
        ),
    )

    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=16,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3600000.0,
        ),
    )

    retrieved = RetrievedRasterArtifact(
        source=RemoteRasterArtifact(
            uri="drive://test/artifact.tif",
            format=RasterArtifactFormat.GEOTIFF,
        ),
        local_path=retrieved_path,
    )

    export_request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:test"
        ),
        output_name="artifact",
        grid=grid,
        destination=(
            EarthEngineExportDestination.DRIVE
        ),
        destination_folder="test",
    )

    with pytest.raises(
        ValueError,
        match="Inspected raster path must match",
    ):
        create_complete_real_image_manifest(
            scene_preparation=scene_preparation,
            composite_request=composite_request,
            export_request=export_request,
            export_task=EarthEngineExportTaskReference(
                task_id="task-123"
            ),
            retrieved_artifact=retrieved,
            inspected_metadata=inspected,
            approved_grid=grid,
        )