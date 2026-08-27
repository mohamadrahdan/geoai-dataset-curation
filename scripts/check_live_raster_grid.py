from pathlib import Path
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)
from geoai_dataset_curation.image_construction.raster_grid_verification import (
    verify_raster_against_grid,
)


ARTIFACT_PATH = Path("artifacts/live/tiny_live_export_smoke.tif")
APPROVED_GRID = RasterGridSpec(
    crs="EPSG:32639",
    width=97,
    height=112,
    pixel_size_x=10.0,
    pixel_size_y=10.0,
    transform=AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=547020.0,
        d=0.0,
        e=-10.0,
        f=3374300.0,
    ),
)


def main() -> int:
    metadata = inspect_raster_artifact(
        ARTIFACT_PATH
    )
    result = verify_raster_against_grid(
        metadata,
        APPROVED_GRID,
    )
    print(f"CRS matches: {result.crs_matches}")
    print(f"Width matches: {result.width_matches}")
    print(f"Height matches: {result.height_matches}")
    print(f"Transform matches: {result.transform_matches}")

    if not result.matches:
        print(
            "FAIL: Retrieved raster does not match "
            "the approved grid."
        )
        return 1

    print(
        "PASS: Retrieved raster exactly matches "
        "the approved grid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )