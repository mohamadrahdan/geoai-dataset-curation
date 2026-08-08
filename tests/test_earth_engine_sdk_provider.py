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


class FakeEarthEngineSdk:
    Filter = FakeFilter

    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or {
            "features": [],
        }
        self.error = error
        self.calls: list[tuple[str, Any]] = []

    def Geometry(
        self,
        geojson: dict[str, object],
    ) -> dict[str, object]:
        self.calls.append(("Geometry", geojson))
        return geojson

    def ImageCollection(
        self,
        collection_id: str,
    ) -> FakeCollection:
        if self.error is not None:
            raise self.error

        self.calls.append(
            (
                "ImageCollection",
                collection_id,
            )
        )

        return FakeCollection(
            result=self.result,
            calls=self.calls,
        )

    def Date(
        self,
        value: Any,
    ) -> FakeDate:
        self.calls.append(("Date", value))
        return FakeDate(value)


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