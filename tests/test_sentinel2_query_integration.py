from __future__ import annotations
from datetime import date
from typing import Any
from shapely.geometry import Polygon
from geoai_dataset_curation.image_construction import (
    EarthEngineSceneReference,
    EarthEngineSdkProvider,
    EarthEngineService,
)
from geoai_dataset_curation.scene_preparation import (
    SceneSelectionRequest,
    StudyAreaSpec,
    build_sentinel2_scene_query,
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

    def __init__(self) -> None:
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
        self.calls.append(
            (
                "ImageCollection",
                collection_id,
            )
        )

        return FakeCollection(
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
            },
            calls=self.calls,
        )

    def Date(
        self,
        value: Any,
    ) -> FakeDate:
        self.calls.append(("Date", value))
        return FakeDate(value)


def test_study_area_query_reaches_sdk_provider_and_returns_scene() -> None:
    study_area = StudyAreaSpec(
        study_area_id="study-area-loop-1",
        source_id="validated-boundary-source",
        crs="EPSG:4326",
        geometry=Polygon(
            [
                (51.0, 30.0),
                (51.2, 30.0),
                (51.2, 30.2),
                (51.0, 30.2),
                (51.0, 30.0),
            ]
        ),
    )

    request = SceneSelectionRequest(
        source_id="validated-boundary-source",
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        collection="COPERNICUS/S2_SR_HARMONIZED",
        required_bands=("B02", "B03", "B04", "B08"),
        max_cloud_cover=20.0,
    )

    query = build_sentinel2_scene_query(
        study_area=study_area,
        request=request,
    )

    sdk = FakeEarthEngineSdk()
    provider = EarthEngineSdkProvider(sdk=sdk)
    service = EarthEngineService(provider)
    scenes = service.search_sentinel2_scenes(query)
    assert scenes == (
        EarthEngineSceneReference(
            scene_id=(
                "COPERNICUS/S2_SR_HARMONIZED/"
                "20240518T064621_example"
            ),
            acquisition_date="2024-05-18",
            cloud_cover=8.5,
        ),
    )
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