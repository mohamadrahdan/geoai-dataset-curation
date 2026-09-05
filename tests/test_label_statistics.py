import numpy as np
import pytest
from geoai_dataset_curation.label_rasterization import (
    compute_label_pixel_statistics,
)


def test_label_statistics_measure_supervision_distribution() -> None:
    data = np.array(
        [
            [255, 255, 1],
            [0, 1, 0],
        ],
        dtype=np.uint8,
    )
    result = compute_label_pixel_statistics(data)
    assert result.total_pixels == 6
    assert result.negative_pixels == 2
    assert result.positive_pixels == 2
    assert result.ignore_pixels == 2
    assert result.supervised_pixels == 4
    assert result.supervised_fraction == pytest.approx(4 / 6)
    assert result.positive_fraction_of_supervised == pytest.approx(0.5)
    assert result.negative_fraction_of_supervised == pytest.approx(0.5)


def test_label_statistics_reject_unapproved_values() -> None:
    data = np.array(
        [
            [0, 1],
            [7, 255],
        ],
        dtype=np.uint8,
    )
    with pytest.raises(
        ValueError,
        match="outside the approved schema",
    ):
        compute_label_pixel_statistics(data)