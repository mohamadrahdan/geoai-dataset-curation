"Label-aware analysis of candidate tile layouts"
from dataclasses import dataclass
import numpy as np
from geoai_dataset_curation.contracts import (
    LabelValue,
)
from geoai_dataset_curation.tiling.contracts import (
    TilingRequest,
)
from geoai_dataset_curation.tiling.identity import (
    build_tile_layout_id,
)
from geoai_dataset_curation.tiling.window_generation import (
    generate_tile_windows,
)


@dataclass(frozen=True)
class TileLabelAnalysis:
    "Supervision measurements for one candidate tile layout"
    layout_id: str
    tile_count: int
    supervised_tile_count: int
    positive_tile_count: int
    negative_only_tile_count: int
    all_ignore_tile_count: int
    source_positive_pixel_count: int
    source_negative_pixel_count: int
    unique_positive_pixels_covered: int
    unique_negative_pixels_covered: int
    positive_pixel_observations: int
    negative_pixel_observations: int
    ignore_pixel_observations: int
    padded_ignore_pixel_observations: int
    positive_tiles_at_least_one_percent: int
    positive_tiles_at_least_five_percent: int

    @property
    def positive_coverage_ratio(self) -> float:
        "Return the fraction of source-positive pixels covered"
        if self.source_positive_pixel_count == 0:
            return 0.0

        return (
            self.unique_positive_pixels_covered
            / self.source_positive_pixel_count
        )

    @property
    def negative_coverage_ratio(self) -> float:
        "Return the fraction of source-negative pixels covered"
        if self.source_negative_pixel_count == 0:
            return 0.0

        return (
            self.unique_negative_pixels_covered
            / self.source_negative_pixel_count
        )

    @property
    def positive_observation_multiplier(self) -> float:
        "Return repeated positive observations per unique positive pixel"
        if self.unique_positive_pixels_covered == 0:
            return 0.0

        return (
            self.positive_pixel_observations
            / self.unique_positive_pixels_covered
        )


def _validate_label_array(
    labels: np.ndarray,
    request: TilingRequest,
) -> None:
    "Validate a label array before tile-level analysis"

    expected_shape = (
        request.grid.height,
        request.grid.width,
    )

    if labels.ndim != 2:
        raise ValueError("labels must be a two-dimensional array.")

    if labels.shape != expected_shape:
        raise ValueError("labels shape must match the request grid.")
    observed_values = {
        int(value)
        for value in np.unique(labels)
    }
    allowed_values = {
        int(LabelValue.NEGATIVE),
        int(LabelValue.POSITIVE),
        int(LabelValue.IGNORE),
    }

    if not observed_values.issubset(
        allowed_values
    ):
        raise ValueError(
            "labels contain values outside the "
            "Loop 1 label contract."
        )


def analyze_label_tiles(
    labels: np.ndarray,
    request: TilingRequest,
) -> TileLabelAnalysis:
    "Measure supervision distribution across candidate windows"
    _validate_label_array(
        labels,
        request,
    )
    windows = generate_tile_windows(
        request
    )

    positive_value = int(
        LabelValue.POSITIVE
    )
    negative_value = int(
        LabelValue.NEGATIVE
    )
    ignore_value = int(
        LabelValue.IGNORE
    )

    coverage_mask = np.zeros(
        labels.shape,
        dtype=bool,
    )

    supervised_tile_count = 0
    positive_tile_count = 0
    negative_only_tile_count = 0
    all_ignore_tile_count = 0

    positive_pixel_observations = 0
    negative_pixel_observations = 0
    ignore_pixel_observations = 0
    padded_ignore_pixel_observations = 0

    positive_tiles_at_least_one_percent = 0
    positive_tiles_at_least_five_percent = 0

    for window in windows:
        row_start = window.row_offset_pixels
        row_end = (
            row_start
            + window.read_height_pixels
        )
        column_start = window.column_offset_pixels
        column_end = (
            column_start
            + window.read_width_pixels
        )

        tile_labels = labels[
            row_start:row_end,
            column_start:column_end,
        ]

        coverage_mask[
            row_start:row_end,
            column_start:column_end,
        ] = True

        positive_count = int(
            np.count_nonzero(
                tile_labels == positive_value
            )
        )
        negative_count = int(
            np.count_nonzero(
                tile_labels == negative_value
            )
        )
        ignore_count = int(
            np.count_nonzero(
                tile_labels == ignore_value
            )
        )

        output_pixel_count = (
            window.output_width_pixels
            * window.output_height_pixels
        )
        read_pixel_count = (
            window.read_width_pixels
            * window.read_height_pixels
        )
        padded_pixel_count = (
            output_pixel_count
            - read_pixel_count
        )

        positive_pixel_observations += (
            positive_count
        )
        negative_pixel_observations += (
            negative_count
        )
        ignore_pixel_observations += (
            ignore_count
            + padded_pixel_count
        )
        padded_ignore_pixel_observations += (
            padded_pixel_count
        )

        supervised_count = (
            positive_count
            + negative_count
        )

        if supervised_count == 0:
            all_ignore_tile_count += 1
        else:
            supervised_tile_count += 1

        if positive_count > 0:
            positive_tile_count += 1

            positive_fraction = (
                positive_count
                / output_pixel_count
            )

            if positive_fraction >= 0.01:
                positive_tiles_at_least_one_percent += 1

            if positive_fraction >= 0.05:
                positive_tiles_at_least_five_percent += 1

        elif negative_count > 0:
            negative_only_tile_count += 1

    source_positive_pixel_count = int(
        np.count_nonzero(
            labels == positive_value
        )
    )
    source_negative_pixel_count = int(
        np.count_nonzero(
            labels == negative_value
        )
    )

    covered_labels = labels[
        coverage_mask
    ]

    unique_positive_pixels_covered = int(
        np.count_nonzero(
            covered_labels == positive_value
        )
    )
    unique_negative_pixels_covered = int(
        np.count_nonzero(
            covered_labels == negative_value
        )
    )

    return TileLabelAnalysis(
        layout_id=build_tile_layout_id(
            request.layout
        ),
        tile_count=len(windows),
        supervised_tile_count=(
            supervised_tile_count
        ),
        positive_tile_count=positive_tile_count,
        negative_only_tile_count=(
            negative_only_tile_count
        ),
        all_ignore_tile_count=(
            all_ignore_tile_count
        ),
        source_positive_pixel_count=(
            source_positive_pixel_count
        ),
        source_negative_pixel_count=(
            source_negative_pixel_count
        ),
        unique_positive_pixels_covered=(
            unique_positive_pixels_covered
        ),
        unique_negative_pixels_covered=(
            unique_negative_pixels_covered
        ),
        positive_pixel_observations=(
            positive_pixel_observations
        ),
        negative_pixel_observations=(
            negative_pixel_observations
        ),
        ignore_pixel_observations=(
            ignore_pixel_observations
        ),
        padded_ignore_pixel_observations=(
            padded_ignore_pixel_observations
        ),
        positive_tiles_at_least_one_percent=(
            positive_tiles_at_least_one_percent
        ),
        positive_tiles_at_least_five_percent=(
            positive_tiles_at_least_five_percent
        ),
    )