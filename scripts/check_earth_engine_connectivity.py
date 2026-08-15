from __future__ import annotations

import os
import sys

import ee

from geoai_dataset_curation.image_construction import (
    PROJECT_ID_ENV,
)


def main() -> int:
    project_id = os.environ.get(
        PROJECT_ID_ENV,
        "",
    ).strip()

    if not project_id:
        print(
            f"FAIL: {PROJECT_ID_ENV} is not set."
        )
        return 2

    print(
        f"Project: {project_id}"
    )

    try:
        ee.Initialize(
            project=project_id
        )
    except Exception as exc:
        print(
            "FAIL: Earth Engine initialization failed."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 3

    print(
        "PASS: Earth Engine initialization succeeded."
    )

    try:
        server_value = ee.Number(
            1
        ).add(
            1
        ).getInfo()
    except Exception as exc:
        print(
            "FAIL: Earth Engine server request failed."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 4

    print(
        "PASS: Earth Engine server request succeeded."
    )
    print(
        f"Server result: {server_value}"
    )

    try:
        scene_count = (
            ee.ImageCollection(
                "COPERNICUS/S2_SR_HARMONIZED"
            )
            .filterDate(
                "2024-05-01",
                "2024-05-02",
            )
            .limit(1)
            .size()
            .getInfo()
        )
    except Exception as exc:
        print(
            "FAIL: Sentinel-2 catalog request failed."
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 5

    print(
        "PASS: Sentinel-2 catalog request succeeded."
    )
    print(
        f"Returned collection size: {scene_count}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )