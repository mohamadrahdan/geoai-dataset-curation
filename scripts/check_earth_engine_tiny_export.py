from __future__ import annotations
import os
import sys
import time
import ee
from geoai_dataset_curation.image_construction import (
    PROJECT_ID_ENV,
)


EXPORT_FOLDER = "geoai-dataset-curation-smoke"
EXPORT_NAME = "tiny_live_export_smoke"
POLL_INTERVAL_SECONDS = 5
MAX_POLLS = 60


def main() -> int:
    project_id = os.environ.get(
        PROJECT_ID_ENV,
        "",
    ).strip()

    if not project_id:
        print(f"FAIL: {PROJECT_ID_ENV} is not set.")
        return 2

    print(f"Project: {project_id}")

    try:
        ee.Initialize(
            project=project_id
        )
    except Exception as exc:
        print("FAIL: Earth Engine initialization failed.")
        print(f"{type(exc).__name__}: {exc}")
        return 3

    print("PASS: Earth Engine initialization succeeded.")

    try:
        image = (
            ee.ImageCollection(
                "COPERNICUS/S2_SR_HARMONIZED"
            )
            .filterDate(
                "2024-05-01",
                "2024-05-31",
            )
            .filterBounds(
                ee.Geometry.Point(
                    [
                        51.5,
                        30.5,
                    ]
                )
            )
            .select(
                [
                    "B2",
                    "B3",
                    "B4",
                    "B8",
                ]
            )
            .median()
        )

        region = ee.Geometry.Rectangle(
            [
                51.49,
                30.49,
                51.50,
                30.50,
            ],
            "EPSG:4326",
            False,
        )

        task = ee.batch.Export.image.toDrive(
            image=image,
            description=EXPORT_NAME,
            folder=EXPORT_FOLDER,
            fileNamePrefix=EXPORT_NAME,
            region=region,
            crs="EPSG:32639",
            crsTransform=[
                10.0,
                0.0,
                355000.0,
                0.0,
                -10.0,
                3375000.0,
            ],
            fileFormat="GeoTIFF",
            maxPixels=1_000_000,
        )
        task.start()

    except Exception as exc:
        print("FAIL: Earth Engine export task could not be started.")
        print(f"{type(exc).__name__}: {exc}")
        return 4

    print(f"PASS: Export task started: {task.id}")

    for poll_number in range(
        1,
        MAX_POLLS + 1,
    ):
        try:
            status = task.status()
        except Exception as exc:
            print("FAIL: Export task status could not be retrieved.")
            print(f"{type(exc).__name__}: {exc}")
            return 5

        state = status.get(
            "state",
            "UNKNOWN",
        )

        print(f"Poll {poll_number}: {state}")

        if state == "COMPLETED":
            print("PASS: Tiny Earth Engine export completed.")
            print(f"Drive folder: {EXPORT_FOLDER}")
            print(f"File prefix: {EXPORT_NAME}")
            return 0

        if state in {
            "FAILED",
            "CANCELLED",
        }:
            print("FAIL: Tiny Earth Engine export did not complete.")
            print(f"Status: {status}")
            return 6

        time.sleep(
            POLL_INTERVAL_SECONDS
        )

    print("FAIL: Export task did not finish within the polling window.")
    return 7


if __name__ == "__main__":
    sys.exit(
        main()
    )