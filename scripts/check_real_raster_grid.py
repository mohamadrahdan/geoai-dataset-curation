"Live check for the exact raster grid of the real study area."
from __future__ import annotations
import os
from pathlib import Path
from geoai_dataset_curation.image_construction.grid_geometry import (
    derive_raster_bounds,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.image_construction.runtime_grid import (
    build_exact_raster_grid_from_study_area,
)
from geoai_dataset_curation.scene_preparation.study_area_loading import (
    load_study_area,
)


def main() -> None:
    "Build and inspect the exact raster grid for the real study area."
    study_area_path = Path(os.environ["GEOAI_STUDY_AREA_PATH"])
    study_area = load_study_area(
        path=study_area_path,
        study_area_id="komeh-study-area",
        source_id="padena_aoi",
    )

    grid = build_exact_raster_grid_from_study_area(
        study_area=study_area,
        target_crs="EPSG:32639",
        pixel_size=10.0,
    )

    bounds = derive_raster_bounds(grid)
    grid_id = build_raster_grid_id(grid)

    if grid.transform is None:
        raise RuntimeError(
            "Exact raster grid unexpectedly has no affine transform."
        )

    print(f"Study area: {study_area.study_area_id}")
    print(f"Source CRS: {study_area.crs}")
    print(f"Target CRS: {grid.crs}")
    print(f"Pixel size: {grid.pixel_size_x} m")
    print(f"Width: {grid.width}")
    print(f"Height: {grid.height}")

    print()
    print("Raster bounds:")
    print(f"Left: {bounds.left}")
    print(f"Bottom: {bounds.bottom}")
    print(f"Right: {bounds.right}")
    print(f"Top: {bounds.top}")

    print()
    print("Affine transform:")
    print(grid.transform.as_tuple)

    print()
    print(f"Grid ID: {grid_id}")

    print()
    print("PASS: Real exact raster grid was constructed successfully.")


if __name__ == "__main__":
    main()