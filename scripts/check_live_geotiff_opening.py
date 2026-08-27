from pathlib import Path
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)


ARTIFACT_PATH = Path(
    "artifacts/live/tiny_live_export_smoke.tif"
)


def main() -> int:
    metadata = inspect_raster_artifact(
        ARTIFACT_PATH
    )

    print("PASS: GeoTIFF opened successfully.")
    print(f"Driver: {metadata.driver}")
    print(f"CRS: {metadata.crs}")
    print(f"Width: {metadata.width}")
    print(f"Height: {metadata.height}")
    print(f"Band count: {metadata.band_count}")
    print(f"Dtypes: {metadata.dtypes}")
    print(f"Transform: {metadata.transform}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )