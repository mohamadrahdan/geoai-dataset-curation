from __future__ import annotations
from typing import Any
from geoai_dataset_curation.image_construction import (
    AffineTransformSpec,
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineService,
    EarthEngineSdkProvider,
    EarthEngineTaskState,
    RasterGridSpec,
    Sentinel2CloudMaskSpec,
)


class FakeSclImage:
    def remap(
        self,
        from_values: list[int],
        to_values: list[int],
        default_value: int,
    ) -> object:
        assert from_values == [
            1,
            3,
            8,
            9,
            10,
            11,
        ]
        assert to_values == [
            0,
            0,
            0,
            0,
            0,
            0,
        ]
        assert default_value == 1
        return "clear-mask"


class FakeImage:
    def __init__(
        self,
        scene_id: str,
    ) -> None:
        self.scene_id = scene_id
        self.scl = FakeSclImage()
        self.selected_bands: list[str] = []
        self.applied_masks: list[object] = []

    def select(
        self,
        bands: str | list[str],
    ) -> object:
        if isinstance(bands, str):
            return self.scl

        self.selected_bands.extend(
            bands
        )
        return self
    
    def updateMask(
        self,
        mask: object,
    ) -> FakeImage:
        self.applied_masks.append(
            mask
        )
        return self


class FakeCompositeCollection:
    def __init__(
        self,
        images: list[object],
    ) -> None:
        self.images = images

    def median(self) -> object:
        return object()


class FakeImageCollectionFactory:
    def fromImages(
        self,
        images: list[object],
    ) -> FakeCompositeCollection:
        return FakeCompositeCollection(
            images
        )


class FakeGeometryFactory:
    def Rectangle(
        self,
        coords: list[float],
        crs: str,
        geodesic: bool,
    ) -> object:
        assert coords == [
            500000.0,
            3594880.0,
            505120.0,
            3600000.0,
        ]
        assert crs == "EPSG:32639"
        assert geodesic is False
        return "export-region"


class FakeExportTask:
    def __init__(self) -> None:
        self.id = "task-integration-1"
        self.start_calls = 0
        self.status_calls = 0
    def start(self) -> None:
        self.start_calls += 1
    def status(
        self,
    ) -> dict[str, object]:
        self.status_calls += 1
        return {
            "state": "COMPLETED",
        }


class FakeDriveExporter:
    def __init__(self) -> None:
        self.last_task: FakeExportTask | None = None
        self.calls: list[
            dict[str, object]
        ] = []
    def toDrive(
        self,
        **kwargs: object,
    ) -> FakeExportTask:
        self.calls.append(
            dict(kwargs)
        )
        task = FakeExportTask()
        self.last_task = task
        return task


class FakeExportNamespace:
    def __init__(self) -> None:
        self.image = FakeDriveExporter()


class FakeBatchNamespace:
    def __init__(self) -> None:
        self.Export = FakeExportNamespace()


class FakeEarthEngineSdk:
    def __init__(self) -> None:
        self.images: dict[str, FakeImage] = {
            "scene-1": FakeImage(
                "scene-1"
            ),
            "scene-2": FakeImage(
                "scene-2"
            ),
        }
        self.ImageCollection = (
            FakeImageCollectionFactory()
        )
        self.Geometry = (
            FakeGeometryFactory()
        )
        self.batch = FakeBatchNamespace()
    def Image(
        self,
        scene_id: str,
    ) -> FakeImage:
        return self.images[
            scene_id
        ]


def test_service_builds_composite_starts_export_and_reads_status() -> None:
    sdk = FakeEarthEngineSdk()
    provider = EarthEngineSdkProvider(
        sdk=sdk
    )
    service = EarthEngineService(
        provider
    )
    composite_request = (
        EarthEngineCompositeRequest(
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
            cloud_mask=(
                Sentinel2CloudMaskSpec()
            ),
            aggregation_method=(
                EarthEngineAggregationMethod.MEDIAN
            ),
        )
    )
    image_reference = (
        service.build_composite(
            composite_request
        )
    )
    export_request = (
        EarthEngineExportRequest(
            image=image_reference,
            output_name=(
                "sentinel2_stack"
            ),
            grid=RasterGridSpec(
                crs="EPSG:32639",
                width=512,
                height=512,
                pixel_size_x=10.0,
                pixel_size_y=10.0,
                transform=(
                    AffineTransformSpec(
                        a=10.0,
                        b=0.0,
                        c=500000.0,
                        d=0.0,
                        e=-10.0,
                        f=3600000.0,
                    )
                ),
            ),
            destination=(
                EarthEngineExportDestination.DRIVE
            ),
            destination_folder=(
                "geoai-dataset-curation"
            ),
        )
    )
    task_reference = (
        service.start_export(
            export_request
        )
    )
    status = service.get_export_status(
        task_reference
    )
    assert task_reference.task_id == (
        "task-integration-1"
    )
    assert (
        status.state
        is EarthEngineTaskState.COMPLETED
    )
    assert status.succeeded is True
    exporter = (
        sdk.batch.Export.image
    )
    assert len(
        exporter.calls
    ) == 1
    task = exporter.last_task
    assert task is not None
    assert task.start_calls == 1
    assert task.status_calls == 1