import numpy as np
import pytest
from shapely.geometry import box
from geoai_dataset_curation.contracts import (
    SupervisionKind,
)
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelVectorSource,
)
from geoai_dataset_curation.sampling import (
    rasterize_negative_source_mask,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=4,
        height=4,
        pixel_size_x=1.0,
        pixel_size_y=1.0,
        transform=AffineTransformSpec(
            a=1.0,
            b=0.0,
            c=0.0,
            d=0.0,
            e=-1.0,
            f=4.0,
        ),
    )


def make_source(
    supervision: SupervisionKind,
) -> LabelVectorSource:
    return LabelVectorSource(
        source_id=f"{supervision.value}-source",
        supervision=supervision,
        geometries=(
            box(
                0.0,
                2.0,
                2.0,
                4.0,
            ),
        ),
    )


@pytest.mark.parametrize(
    "supervision",
    [
        SupervisionKind.NEGATIVE_REFERENCE,
        SupervisionKind.HARD_NEGATIVE_REFERENCE,
    ],
)
def test_explicit_negative_source_produces_boolean_mask(
    supervision: SupervisionKind,
) -> None:
    mask = rasterize_negative_source_mask(
        make_source(supervision),
        grid=make_grid(),
    )
    assert mask.shape == (4, 4)
    assert mask.dtype == np.dtype(np.bool_)
    assert int(np.count_nonzero(mask)) == 4


def test_negative_source_mask_preserves_exact_coverage() -> None:
    mask = rasterize_negative_source_mask(
        make_source(
            SupervisionKind.NEGATIVE_REFERENCE
        ),
        grid=make_grid(),
    )
    expected = np.array(
        [
            [True, True, False, False],
            [True, True, False, False],
            [False, False, False, False],
            [False, False, False, False],
        ],
        dtype=bool,
    )
    assert np.array_equal(mask, expected)


def test_positive_source_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "source must use NEGATIVE_REFERENCE or "
            "HARD_NEGATIVE_REFERENCE supervision"
        ),
    ):
        rasterize_negative_source_mask(
            make_source(
                SupervisionKind.POSITIVE_REFERENCE
            ),
            grid=make_grid(),
        )


def test_unlabeled_source_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "source must use NEGATIVE_REFERENCE or "
            "HARD_NEGATIVE_REFERENCE supervision"
        ),
    ):
        rasterize_negative_source_mask(
            make_source(
                SupervisionKind.UNLABELED
            ),
            grid=make_grid(),
        )


def test_invalid_negative_source_is_rejected() -> None:
    source = LabelVectorSource(
        source_id="empty-negative-source",
        supervision=(
            SupervisionKind.NEGATIVE_REFERENCE
        ),
        geometries=(),
    )
    with pytest.raises(
        ValueError,
        match="Invalid label rasterization request",
    ):
        rasterize_negative_source_mask(
            source,
            grid=make_grid(),
        )


def test_repeated_source_mask_rasterization_is_deterministic() -> None:
    source = make_source(
        SupervisionKind.HARD_NEGATIVE_REFERENCE
    )
    grid = make_grid()

    first = rasterize_negative_source_mask(
        source,
        grid=grid,
    )
    second = rasterize_negative_source_mask(
        source,
        grid=grid,
    )
    assert np.array_equal(first, second)