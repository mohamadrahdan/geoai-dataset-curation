"Statistics for Loop 1 label rasters"
from dataclasses import dataclass
import numpy as np
from geoai_dataset_curation.contracts.labels import LabelValue
from geoai_dataset_curation.label_rasterization.artifact_contract import (
    LOOP1_LABEL_ALLOWED_VALUES,
)


@dataclass(frozen=True)
class LabelPixelStatistics:
    "Pixel-level supervision statistics for one label raster"
    total_pixels: int
    negative_pixels: int
    positive_pixels: int
    ignore_pixels: int

    @property
    def supervised_pixels(self) -> int:
        return self.negative_pixels + self.positive_pixels

    @property
    def supervised_fraction(self) -> float:
        if self.total_pixels == 0:
            return 0.0
        return self.supervised_pixels / self.total_pixels

    @property
    def positive_fraction_of_supervised(self) -> float:
        if self.supervised_pixels == 0:
            return 0.0
        return self.positive_pixels / self.supervised_pixels

    @property
    def negative_fraction_of_supervised(self) -> float:
        if self.supervised_pixels == 0:
            return 0.0
        return self.negative_pixels / self.supervised_pixels


def compute_label_pixel_statistics(
    data: np.ndarray,
) -> LabelPixelStatistics:
    "Compute supervision statistics from one label raster"
    if data.ndim != 2:
        raise ValueError("Label statistics require a two-dimensional raster")
    observed_values = set(int(value) for value in np.unique(data))
    unexpected_values = observed_values - set(LOOP1_LABEL_ALLOWED_VALUES)
    if unexpected_values:
        raise ValueError(
            "Label raster contains values outside the approved schema: "
            f"{sorted(unexpected_values)}"
        )

    return LabelPixelStatistics(
        total_pixels=int(data.size),
        negative_pixels=int(
            np.count_nonzero(data == int(LabelValue.NEGATIVE))
        ),
        positive_pixels=int(
            np.count_nonzero(data == int(LabelValue.POSITIVE))
        ),
        ignore_pixels=int(
            np.count_nonzero(data == int(LabelValue.IGNORE))
        ),
    )