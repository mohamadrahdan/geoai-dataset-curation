from __future__ import annotations
from typing import Any
import pytest
from requests.exceptions import ConnectionError
from geoai_dataset_curation.image_construction import (
    EarthEngineConnectionError,
    EarthEngineRequestError,
    EarthEngineSceneQuery,
    EarthEngineSdkProvider,
    EarthEngineProvider,
    AffineTransformSpec,
    EarthEngineExportDestination,
    EarthEngineExportRequest,
    EarthEngineImageReference,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.cloud_mask import (
    Sentinel2CloudMaskSpec,
)
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineAggregationMethod,
    EarthEngineCompositeRequest,
)
from geoai_dataset_curation.image_construction.earth_engine_sdk_provider import (
    _apply_sentinel2_cloud_mask,
    _build_drive_export_parameters,
)


class FakeValue:
    def __init__(self, value: Any) -> None:
        self._value = value
    def getInfo(self) -> Any:
        return self._value


class FakeDate:
    def __init__(self, value: Any) -> None:
        self._value = value
    def format(self, pattern: str) -> FakeValue:
        assert pattern == "YYYY-MM-dd"
        return FakeValue("2024-05-18")


class FakeCollection:
    def __init__(
        self,
        *,
        result: dict[str, Any],
        calls: list[tuple[str, Any]],
    ) -> None:
        self._result = result
        self._calls = calls

    def filterDate(
        self,
        start_date: str,
        end_date: str,
    ) -> FakeCollection:
        self._calls.append(
            (
                "filterDate",
                (start_date, end_date),
            )
        )
        return self

    def filterBounds(
        self,
        geometry: Any,
    ) -> FakeCollection:
        self._calls.append(
            (
                "filterBounds",
                geometry,
            )
        )
        return self

    def filter(
        self,
        expression: Any,
    ) -> FakeCollection:
        self._calls.append(
            (
                "filter",
                expression,
            )
        )
        return self

    def sort(
        self,
        property_name: str,
    ) -> FakeCollection:
        self._calls.append(
            (
                "sort",
                property_name,
            )
        )
        return self

    def getInfo(self) -> dict[str, Any]:
        self._calls.append(("getInfo", None))
        return self._result


class FakeFilter:
    @staticmethod
    def lte(
        property_name: str,
        value: float,
    ) -> tuple[str, str, float]:
        return (
            "lte",
            property_name,
            value,
        )


class FakeSclImage:
    def __init__(self) -> None:
        self.remap_calls: list[
            tuple[list[int], list[int], int]
        ] = []

    def remap(
        self,
        from_values: list[int],
        to_values: list[int],
        default_value: int,
    ) -> object:
        self.remap_calls.append(
            (
                from_values,
                to_values,
                default_value,
            )
        )
        return "clear-mask"


class FakeMaskableImage:
    def __init__(self) -> None:
        self.scl = FakeSclImage()
        self.selected_bands: list[str] = []
        self.update_mask_calls: list[object] = []

    def select(
        self,
        bands: str | list[str],
    ) -> object:
        if isinstance(bands, str):
            self.selected_bands.append(bands)
            return self.scl

        self.selected_bands.extend(bands)
        return self

    def updateMask(
        self,
        mask: object,
    ) -> "FakeMaskableImage":
        self.update_mask_calls.append(mask)
        return self
    

class FakeCompositeCollection:
    def __init__(
        self,
        images: list[object],
    ) -> None:
        self.images = images
        self.median_calls = 0

    def median(self) -> str:
        self.median_calls += 1
        return "median-composite"


class FakeImageCollectionFactory:
    def __init__(
        self,
        *,
        result: dict[str, Any],
        error: Exception | None,
        calls: list[tuple[str, Any]],
    ) -> None:
        self._result = result
        self._error = error
        self._calls = calls
        self.from_images_calls: list[list[object]] = []
        self.last_collection: FakeCompositeCollection | None = None

    def __call__(
        self,
        collection_id: str,
    ) -> FakeCollection:
        if self._error is not None:
            raise self._error

        self._calls.append(
            (
                "ImageCollection",
                collection_id,
            )
        )

        return FakeCollection(
            result=self._result,
            calls=self._calls,
        )

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
    Filter = FakeFilter
    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.images: dict[str, object] = {}
        self.result = result or {
            "features": [],
        }
        self.error = error
        self.calls: list[tuple[str, Any]] = []
        self.Geometry = FakeGeometryFactory(self.calls)
        self.ImageCollection = FakeImageCollectionFactory(
            result=self.result,
            error=self.error,
            calls=self.calls,
        )

    def Date(
        self,
        value: Any,
    ) -> FakeDate:
        self.calls.append(
            (
                "Date",
                value,
            )
        )
        return FakeDate(value)
    def Image(
        self,
        scene_id: str,
    ) -> object:
        return self.images[scene_id]


class FakeGeometryFactory:
    def __init__(
        self,
        calls: list[tuple[str, Any]],
    ) -> None:
        self._calls = calls
        self.rectangle_calls: list[
            tuple[list[float], str, bool]
        ] = []

    def __call__(
        self,
        geojson: dict[str, object],
    ) -> dict[str, object]:
        self._calls.append(
            (
                "Geometry",
                geojson,
            )
        )
        return geojson
    def Rectangle(
        self,
        coords: list[float],
        crs: str,
        geodesic: bool,
    ) -> object:
        self.rectangle_calls.append(
            (
                coords,
                crs,
                geodesic,
            )
        )
        return "export-region"

def _query() -> EarthEngineSceneQuery:
    return EarthEngineSceneQuery(
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
        start_date="2024-04-01",
        end_date="2024-06-30",
        aoi_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [51.0, 30.0],
                    [51.2, 30.0],
                    [51.2, 30.2],
                    [51.0, 30.2],
                    [51.0, 30.0],
                ]
            ],
        },
        maximum_cloud_cover=20.0,
    )


def test_sdk_provider_builds_expected_scene_query() -> None:
    sdk = FakeEarthEngineSdk()
    provider = EarthEngineSdkProvider(sdk=sdk)
    result = provider.search_sentinel2_scenes(_query())
    assert result == ()
    assert (
        "ImageCollection",
        "COPERNICUS/S2_SR_HARMONIZED",
    ) in sdk.calls
    assert (
        "filterDate",
        (
            "2024-04-01",
            "2024-07-01",
        ),
    ) in sdk.calls
    assert (
        "filter",
        (
            "lte",
            "CLOUDY_PIXEL_PERCENTAGE",
            20.0,
        ),
    ) in sdk.calls
    assert (
        "sort",
        "system:time_start",
    ) in sdk.calls


def test_sdk_provider_normalizes_scene_metadata() -> None:
    sdk = FakeEarthEngineSdk(
        result={
            "features": [
                {
                    "id": (
                        "COPERNICUS/S2_SR_HARMONIZED/"
                        "20240518T064621_example"
                    ),
                    "properties": {
                        "system:index": (
                            "20240518T064621_example"
                        ),
                        "system:time_start": 1716014781000,
                        "CLOUDY_PIXEL_PERCENTAGE": 8.5,
                    },
                }
            ]
        }
    )
    provider = EarthEngineSdkProvider(sdk=sdk)
    result = provider.search_sentinel2_scenes(_query())
    assert len(result) == 1
    scene = result[0]
    assert scene.scene_id == (
        "COPERNICUS/S2_SR_HARMONIZED/"
        "20240518T064621_example"
    )
    assert scene.acquisition_date == "2024-05-18"
    assert scene.cloud_cover == 8.5


def test_sdk_provider_returns_empty_result() -> None:
    sdk = FakeEarthEngineSdk(
        result={
            "features": [],
        }
    )
    provider = EarthEngineSdkProvider(sdk=sdk)
    result = provider.search_sentinel2_scenes(_query())
    assert result == ()


def test_sdk_provider_rejects_incomplete_scene_metadata() -> None:
    sdk = FakeEarthEngineSdk(
        result={
            "features": [
                {
                    "id": "scene-1",
                    "properties": {
                        "system:time_start": 1716014781000,
                    },
                }
            ]
        }
    )
    provider = EarthEngineSdkProvider(sdk=sdk)
    with pytest.raises(
        EarthEngineRequestError,
        match="scene metadata is incomplete",
    ):
        provider.search_sentinel2_scenes(_query())


def test_sdk_provider_normalizes_connection_failure() -> None:
    sdk = FakeEarthEngineSdk(
        error=ConnectionError(
            "network unavailable"
        )
    )
    provider = EarthEngineSdkProvider(sdk=sdk)
    with pytest.raises(
        EarthEngineConnectionError,
        match="scene search could not reach",
    ):
        provider.search_sentinel2_scenes(_query())


def test_sdk_provider_normalizes_sdk_failure() -> None:
    sdk = FakeEarthEngineSdk(
        error=RuntimeError(
            "Earth Engine rejected request"
        )
    )
    provider = EarthEngineSdkProvider(sdk=sdk)
    with pytest.raises(
        EarthEngineRequestError,
        match="Earth Engine scene search failed",
    ):
        provider.search_sentinel2_scenes(_query())


def test_sdk_provider_satisfies_provider_protocol() -> None:
    provider = EarthEngineSdkProvider(
        sdk=FakeEarthEngineSdk()
    )
    assert isinstance(provider, EarthEngineProvider)


def test_cloud_masking_translates_default_policy_to_sdk_operations() -> None:
    image = FakeMaskableImage()
    spec = Sentinel2CloudMaskSpec()

    result = _apply_sentinel2_cloud_mask(
        image,
        spec,
    )
    assert image.selected_bands == ["SCL"]
    assert image.scl.remap_calls == [
        (
            [1, 3, 8, 9, 10, 11],
            [0, 0, 0, 0, 0, 0],
            1,
        )
    ]
    assert image.update_mask_calls == [
        "clear-mask"
    ]
    #assert result == "masked-image"
    assert result is image


def test_cloud_masking_respects_custom_excluded_classes() -> None:
    image = FakeMaskableImage()
    spec = Sentinel2CloudMaskSpec(
        scl_band="CUSTOM_SCL",
        excluded_scl_classes=(3, 8, 9),
    )
    _apply_sentinel2_cloud_mask(
        image,
        spec,
    )
    assert image.selected_bands == [
        "CUSTOM_SCL"
    ]
    assert image.scl.remap_calls == [
        (
            [3, 8, 9],
            [0, 0, 0],
            1,
        )
    ]

def test_sdk_provider_builds_median_composite() -> None:
    sdk = FakeEarthEngineSdk()

    scene_1 = FakeMaskableImage()
    scene_2 = FakeMaskableImage()

    sdk.images = {
        "scene-1": scene_1,
        "scene-2": scene_2,
    }

    provider = EarthEngineSdkProvider(
        sdk=sdk
    )

    request = EarthEngineCompositeRequest(
        scene_ids=("scene-1", "scene-2"),
        bands=("B2", "B3", "B4", "B8"),
        cloud_mask=Sentinel2CloudMaskSpec(),
        aggregation_method=EarthEngineAggregationMethod.MEDIAN,
    )

    reference = provider.build_composite(request)

    assert reference.image_id == (
        "sentinel2-composite:median:2-scenes"
    )
    collection = sdk.ImageCollection.last_collection
    assert collection is not None
    assert collection.median_calls == 1

def test_sdk_export_parameters_preserve_exact_grid() -> None:
    sdk = FakeEarthEngineSdk()

    image = object()

    request = EarthEngineExportRequest(
        image=EarthEngineImageReference(
            image_id="composite:test"
        ),
        output_name="sentinel2_stack",
        grid=RasterGridSpec(
            crs="EPSG:32639",
            width=512,
            height=512,
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
        ),
        destination=(
            EarthEngineExportDestination.DRIVE
        ),
        destination_folder=(
            "geoai-dataset-curation"
        ),
    )

    params = _build_drive_export_parameters(
        sdk=sdk,
        image=image,
        request=request,
    )

    assert params["image"] is image
    assert params["description"] == (
        "sentinel2_stack"
    )
    assert params["folder"] == (
        "geoai-dataset-curation"
    )
    assert params["fileNamePrefix"] == (
        "sentinel2_stack"
    )
    assert params["region"] == "export-region"
    assert params["crs"] == "EPSG:32639"
    assert params["crsTransform"] == [
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        3600000.0,
    ]
    assert params["fileFormat"] == "GeoTIFF"
    assert sdk.Geometry.rectangle_calls == [
        (
            [
                500000.0,
                3594880.0,
                505120.0,
                3600000.0,
            ],
            "EPSG:32639",
            False,
        )
    ]
    assert "dimensions" not in params
    assert "scale" not in params