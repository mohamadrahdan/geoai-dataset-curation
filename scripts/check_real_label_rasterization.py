"Live rasterization of real private reference labels"
from pathlib import Path
import numpy as np
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterArtifactSpec,
    LabelRasterizationRequest,
    create_label_raster_artifact_spec,
    rasterize_label_request,
    write_label_raster_artifact,
)
from geoai_dataset_curation.label_rasterization.real_reference_env import (
    load_real_reference_source_configs,
)
from geoai_dataset_curation.label_rasterization.real_reference_wiring import (
    wire_real_reference_sources,
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

OUTPUT_PATH = Path(
    "artifacts/live/loop1/komeh_labels_v1.tif"
)


def main() -> int:
    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )

    wired = wire_real_reference_sources(
        configs=configs,
        target_crs=APPROVED_GRID.crs,
    )

    request = LabelRasterizationRequest(
        sources=tuple(
            result.vector_source
            for result in wired
        ),
        grid=APPROVED_GRID,
        output_name="komeh_labels_v1",
    )

    result = rasterize_label_request(request)
    spec: LabelRasterArtifactSpec = (
        create_label_raster_artifact_spec(
            request
        )
    )

    output_path = write_label_raster_artifact(
        data=result.data,
        spec=spec,
        output_path=OUTPUT_PATH,
    )

    unique_values, counts = np.unique(
        result.data,
        return_counts=True,
    )

    print("Real label rasterization")
    print("========================")
    print(f"Output path: {output_path}")
    print(f"Shape: {result.data.shape}")
    print(f"Dtype: {result.data.dtype}")
    print(
        "Burned feature count: "
        f"{result.burned_feature_count}"
    )

    print()
    print("Observed values:")
    for value, count in zip(
        unique_values,
        counts,
        strict=True,
    ):
        print(
            f"  value={int(value)} "
            f"pixels={int(count)}"
        )

    if result.data.shape != (
        APPROVED_GRID.height,
        APPROVED_GRID.width,
    ):
        print(
            "FAIL: Label raster shape does not "
            "match the approved grid."
        )
        return 1
    if result.data.dtype != np.uint8:
        print("FAIL: Label raster dtype is not uint8.")
        return 1
    if result.burned_feature_count != 160:
        print("FAIL: Expected 160 burned reference features.")
        return 1
    if not set(
        int(value)
        for value in unique_values
    ).issubset({0, 1, 255}):
        print("FAIL: Unexpected label values detected.")
        return 1

    print()
    print(
        "PASS: Real label raster was created "
        "successfully."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )