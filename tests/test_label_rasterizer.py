import numpy as np
import pytest
from shapely.geometry import Polygon

from geoai_dataset_curation.contracts import (
    LabelValue,
    SupervisionKind,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterizationRequest,
    LabelVectorSource,
    rasterize_label_request,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=4,
        height=4,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=0.0,
            d=0.0,
            e=-10.0,
            f=40.0,
        ),
    )


def make_polygon(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
) -> Polygon:
    return Polygon(
        [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
            (min_x, min_y),
        ]
    )


def test_unlabeled_pixels_remain_ignore() -> None:
    source = LabelVectorSource(
        source_id="positive",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(
            make_polygon(
                0.0,
                30.0,
                10.0,
                40.0,
            ),
        ),
    )
    result = rasterize_label_request(
        LabelRasterizationRequest(
            sources=(source,),
            grid=make_grid(),
            output_name="labels",
        )
    )
    assert result.data.dtype == np.uint8
    assert result.data[0, 0] == int(LabelValue.POSITIVE)
    assert result.data[3, 3] == int(LabelValue.IGNORE)


def test_negative_reference_burns_zero() -> None:
    source = LabelVectorSource(
        source_id="negative",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(
            make_polygon(
                10.0,
                30.0,
                20.0,
                40.0,
            ),
        ),
    )
    result = rasterize_label_request(
        LabelRasterizationRequest(
            sources=(source,),
            grid=make_grid(),
            output_name="labels",
        )
    )
    assert result.data[0, 1] == int(LabelValue.NEGATIVE)


def test_hard_negative_burns_zero() -> None:
    source = LabelVectorSource(
        source_id="hard-negative",
        supervision=SupervisionKind.HARD_NEGATIVE_REFERENCE,
        geometries=(
            make_polygon(
                20.0,
                30.0,
                30.0,
                40.0,
            ),
        ),
    )
    result = rasterize_label_request(
        LabelRasterizationRequest(
            sources=(source,),
            grid=make_grid(),
            output_name="labels",
        )
    )
    assert result.data[0, 2] == int(LabelValue.NEGATIVE)


def test_conflicting_targets_are_rejected() -> None:
    polygon = make_polygon(
        0.0,
        30.0,
        10.0,
        40.0,
    )
    positive = LabelVectorSource(
        source_id="positive",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(polygon,),
    )
    negative = LabelVectorSource(
        source_id="negative",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(polygon,),
    )
    request = LabelRasterizationRequest(
        sources=(
            positive,
            negative,
        ),
        grid=make_grid(),
        output_name="labels",
    )
    with pytest.raises(
        ValueError,
        match="Conflicting supervision",
    ):
        rasterize_label_request(request)


def test_same_target_overlap_is_allowed() -> None:
    polygon = make_polygon(
        0.0,
        30.0,
        10.0,
        40.0,
    )
    negative = LabelVectorSource(
        source_id="negative",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(polygon,),
    )
    hard_negative = LabelVectorSource(
        source_id="hard-negative",
        supervision=SupervisionKind.HARD_NEGATIVE_REFERENCE,
        geometries=(polygon,),
    )
    result = rasterize_label_request(
        LabelRasterizationRequest(
            sources=(
                negative,
                hard_negative,
            ),
            grid=make_grid(),
            output_name="labels",
        )
    )
    assert result.data[0, 0] == int(LabelValue.NEGATIVE)