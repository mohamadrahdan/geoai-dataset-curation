from __future__ import annotations
from typing import Any
from geoai_dataset_curation.image_construction import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
    EarthEngineService,
    EarthEngineSdkProvider,
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
            assert bands == "SCL"
            return self.scl

        self.selected_bands.extend(bands)
        return self

    def updateMask(
        self,
        mask: object,
    ) -> FakeImage:
        self.applied_masks.append(mask)
        return self


class FakeCompositeCollection:
    def __init__(
        self,
        images: list[object],
    ) -> None:
        self.images = images
        self.median_calls = 0

    def median(self) -> object:
        self.median_calls += 1
        return object()


class FakeImageCollectionFactory:
    def __init__(self) -> None:
        self.from_images_calls: list[
            list[object]
        ] = []
        self.last_collection: (
            FakeCompositeCollection | None
        ) = None

    def fromImages(
        self,
        images: list[object],
    ) -> FakeCompositeCollection:
        self.from_images_calls.append(images)

        collection = FakeCompositeCollection(
            images
        )
        self.last_collection = collection
        return collection


class FakeEarthEngineSdk:
    def __init__(self) -> None:
        self.images = {
            "scene-1": FakeImage("scene-1"),
            "scene-2": FakeImage("scene-2"),
        }

        self.ImageCollection = (
            FakeImageCollectionFactory()
        )

    def Image(
        self,
        scene_id: str,
    ) -> object:
        return self.images[scene_id]


def test_composite_request_reaches_sdk_provider_and_builds_median() -> None:
    sdk = FakeEarthEngineSdk()
    provider = EarthEngineSdkProvider(
        sdk=sdk
    )

    service = EarthEngineService(
        provider
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

    reference = service.build_composite(
        request
    )
    assert reference.image_id == (
        "sentinel2-composite:median:2-scenes"
    )
    scene_1 = sdk.images["scene-1"]
    scene_2 = sdk.images["scene-2"]
    assert scene_1.applied_masks == [
        "clear-mask"
    ]
    assert scene_2.applied_masks == [
        "clear-mask"
    ]
    assert scene_1.selected_bands == [
        "B2",
        "B3",
        "B4",
        "B8",
    ]
    assert scene_2.selected_bands == [
        "B2",
        "B3",
        "B4",
        "B8",
    ]
    collection = (
        sdk.ImageCollection.last_collection
    )
    assert collection is not None
    assert collection.median_calls == 1