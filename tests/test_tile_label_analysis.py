from pathlib import Path
import numpy as np
import pytest
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    TilingRequest,
    analyze_label_tiles,
)


def make_request(
    *,
    width: int,
    height: int,
    tile_size: int,
    stride: int,
    edge_policy: TileEdgePolicy,
) -> TilingRequest:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=width,
        height=height,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3500000.0,
        ),
    )
    return TilingRequest(
        image_artifact_path=Path("image.tif"),
        label_artifact_path=Path("labels.tif"),
        grid=grid,
        grid_id=build_raster_grid_id(grid),
        layout=TileLayoutSpec(
            tile_width_pixels=tile_size,
            tile_height_pixels=tile_size,
            stride_x_pixels=stride,
            stride_y_pixels=stride,
            edge_policy=edge_policy,
        ),
        output_name="label-analysis",
    )


def test_analysis_classifies_supervision_tiles() -> None:
    labels = np.array(
        [
            [1, 255, 0, 255],
            [1, 255, 0, 255],
            [255, 255, 255, 255],
            [0, 0, 255, 255],
        ],
        dtype=np.uint8,
    )
    request = make_request(
        width=4,
        height=4,
        tile_size=2,
        stride=2,
        edge_policy=TileEdgePolicy.SHIFT_TO_FIT,
    )

    result = analyze_label_tiles(
        labels,
        request,
    )
    assert result.tile_count == 4
    assert result.supervised_tile_count == 3
    assert result.positive_tile_count == 1
    assert result.negative_only_tile_count == 2
    assert result.all_ignore_tile_count == 1
    assert result.source_positive_pixel_count == 2
    assert result.source_negative_pixel_count == 4
    assert result.positive_pixel_observations == 2
    assert result.negative_pixel_observations == 4
    assert result.positive_coverage_ratio == 1.0
    assert result.negative_coverage_ratio == 1.0


def test_overlap_reports_repeated_positive_observations() -> None:
    labels = np.full(
        (3, 3),
        255,
        dtype=np.uint8,
    )
    labels[1, 1] = 1

    request = make_request(
        width=3,
        height=3,
        tile_size=2,
        stride=1,
        edge_policy=TileEdgePolicy.SHIFT_TO_FIT,
    )

    result = analyze_label_tiles(
        labels,
        request,
    )
    assert result.tile_count == 4
    assert result.positive_tile_count == 4
    assert result.source_positive_pixel_count == 1
    assert result.unique_positive_pixels_covered == 1
    assert result.positive_pixel_observations == 4
    assert result.positive_observation_multiplier == 4.0


def test_drop_policy_reports_lost_positive_supervision() -> None:
    labels = np.full(
        (5, 5),
        255,
        dtype=np.uint8,
    )
    labels[4, 4] = 1

    request = make_request(
        width=5,
        height=5,
        tile_size=2,
        stride=2,
        edge_policy=TileEdgePolicy.DROP_PARTIAL,
    )

    result = analyze_label_tiles(
        labels,
        request,
    )
    assert result.source_positive_pixel_count == 1
    assert result.unique_positive_pixels_covered == 0
    assert result.positive_pixel_observations == 0
    assert result.positive_coverage_ratio == 0.0


def test_padding_is_counted_as_ignore_observation() -> None:
    labels = np.full(
        (3, 3),
        255,
        dtype=np.uint8,
    )
    request = make_request(
        width=3,
        height=3,
        tile_size=2,
        stride=2,
        edge_policy=TileEdgePolicy.PAD_PARTIAL,
    )

    result = analyze_label_tiles(
        labels,
        request,
    )
    assert result.tile_count == 4
    assert result.all_ignore_tile_count == 4
    assert result.padded_ignore_pixel_observations == 7
    assert result.ignore_pixel_observations == 16


def test_analysis_rejects_invalid_label_array() -> None:
    request = make_request(
        width=4,
        height=4,
        tile_size=2,
        stride=2,
        edge_policy=TileEdgePolicy.SHIFT_TO_FIT,
    )

    with pytest.raises(
        ValueError,
        match="shape must match",
    ):
        analyze_label_tiles(
            np.zeros(
                (3, 4),
                dtype=np.uint8,
            ),
            request,
        )

    invalid_labels = np.zeros(
        (4, 4),
        dtype=np.uint8,
    )
    invalid_labels[0, 0] = 7

    with pytest.raises(
        ValueError,
        match="outside the Loop 1 label contract",
    ):
        analyze_label_tiles(
            invalid_labels,
            request,
        )