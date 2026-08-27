"Runtime orchestration for end-to-end Earth Engine image construction"
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from geoai_dataset_curation.image_construction.earth_engine_provider import (
    EarthEngineCompositeRequest,
    EarthEngineExportRequest,
    EarthEngineExportTaskReference,
    EarthEngineExportTaskStatus,
    EarthEngineImageReference,
    EarthEngineSceneQuery,
    EarthEngineSceneReference,
)
from geoai_dataset_curation.image_construction.earth_engine_service import (
    EarthEngineService,
)


CompositeRequestFactory = Callable[
    [tuple[EarthEngineSceneReference, ...]],
    EarthEngineCompositeRequest,
]

ExportRequestFactory = Callable[
    [EarthEngineImageReference],
    EarthEngineExportRequest,
]

SleepFunction = Callable[[float], None]


@dataclass(frozen=True)
class EndToEndEarthEngineResult:
    "Result of one successful Earth Engine image-construction execution"
    scenes: tuple[EarthEngineSceneReference, ...]
    composite: EarthEngineImageReference
    export_task: EarthEngineExportTaskReference
    final_status: EarthEngineExportTaskStatus


def execute_earth_engine_image_flow(
    *,
    service: EarthEngineService,
    scene_query: EarthEngineSceneQuery,
    composite_request_factory: CompositeRequestFactory,
    export_request_factory: ExportRequestFactory,
    max_polls: int = 60,
    poll_interval_seconds: float = 5.0,
    sleep_fn: SleepFunction = sleep,
) -> EndToEndEarthEngineResult:
    "Execute scene search, composite construction, export, and polling"
    if max_polls <= 0:
        raise ValueError("max_polls must be greater than zero.")
    if poll_interval_seconds < 0:
        raise ValueError("poll_interval_seconds must not be negative.")
    scenes = service.search_sentinel2_scenes(scene_query)

    if not scenes:
        raise ValueError("No Sentinel-2 scenes were returned.")
    composite_request = composite_request_factory(scenes)
    composite = service.build_composite(composite_request)
    export_request = export_request_factory(composite)
    export_task = service.start_export(export_request)

    for poll_index in range(max_polls):
        status = service.get_export_status(export_task)

        if status.succeeded:
            return EndToEndEarthEngineResult(
                scenes=scenes,
                composite=composite,
                export_task=export_task,
                final_status=status,
            )

        if status.is_terminal:
            raise RuntimeError(
                "Earth Engine export terminated "
                f"with state {status.state.value!r}: "
                f"{status.error_message or 'no error message'}"
            )

        if poll_index < max_polls - 1:
            sleep_fn(poll_interval_seconds)

    raise TimeoutError(
        "Earth Engine export did not complete "
        "within the polling limit."
    )