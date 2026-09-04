"Live verification of the real Loop 1 label-raster artifact"
from pathlib import Path
import numpy as np
import rasterio
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.raster_artifact_inspection import (
    inspect_raster_artifact,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterArtifactSpec,
    verify_label_raster_artifact,
)


ARTIFACT_PATH = Path(
    "artifacts/live/loop1/komeh_labels_v1.tif"
)
APPROVED_GRID = RasterGridSpec(
    crs="EPSG:32639",
    width=5712,
    height=5493,
    pixel_size_x=10.0,
    pixel_size_y=10.0,
    transform=AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=533040.0,
        d=0.0,
        e=-10.0,
        f=3451350.0,
    ),
)


def main() -> int:
    metadata = inspect_raster_artifact(
        ARTIFACT_PATH
    )
    with rasterio.open(ARTIFACT_PATH) as dataset:
        observed_values = tuple(
            int(value)
            for value in np.unique(
                dataset.read(1)
            )
        )
    spec = LabelRasterArtifactSpec(
        output_name="komeh_labels_v1",
        grid=APPROVED_GRID,
    )
    result = verify_label_raster_artifact(
        metadata=metadata,
        observed_values=observed_values,
        spec=spec,
    )

    print("Real label artifact verification")
    print("===============================")
    print(f"Path: {ARTIFACT_PATH}")
    print(f"CRS matches: {result.grid.crs_matches}")
    print(f"Width matches: {result.grid.width_matches}")
    print(f"Height matches: {result.grid.height_matches}")
    print(
        "Transform matches: "
        f"{result.grid.transform_matches}"
    )
    print(
        "Band count matches: "
        f"{result.band_count_matches}"
    )
    print(
        "Dtype matches: "
        f"{result.dtype_matches}"
    )
    print(
        "Values valid: "
        f"{result.values_valid}"
    )
    print(
        "Observed values: "
        f"{observed_values}"
    )
    if not result.matches:
        print(
            "FAIL: Real label artifact does not satisfy "
            "the approved contract."
        )
        return 1

    print(
        "PASS: Real label artifact satisfies "
        "the approved contract."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )