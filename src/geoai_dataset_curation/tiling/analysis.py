"Geometric analysis of candidate tiling layouts"
from dataclasses import dataclass
from geoai_dataset_curation.tiling.identity import (
    build_tile_layout_id,
)
from geoai_dataset_curation.tiling.window_generation import (
    generate_tile_windows,
)
from geoai_dataset_curation.tiling.contracts import (
    TilingRequest,
)


@dataclass(frozen=True)
class TileLayoutAnalysis:
    "Geometric measurements for one candidate tile layout"
    layout_id: str
    tile_count: int
    full_tile_count: int
    partial_tile_count: int
    source_pixel_count: int
    covered_source_pixel_count: int
    uncovered_source_pixel_count: int
    total_read_pixel_count: int
    total_output_pixel_count: int
    padded_output_pixel_count: int
    repeated_read_pixel_count: int

    @property
    def coverage_ratio(self) -> float:
        "Return the fraction of unique source pixels covered"
        return (
            self.covered_source_pixel_count
            / self.source_pixel_count
        )

    @property
    def output_expansion_ratio(self) -> float:
        "Return output pixels relative to unique source pixels"
        return (
            self.total_output_pixel_count
            / self.source_pixel_count
        )


def _covered_axis_length(
    intervals: set[tuple[int, int]],
) -> int:
    "Return the union length of pixel intervals on one axis"
    ordered = sorted(
        (
            offset,
            offset + length,
        )
        for offset, length in intervals
    )
    current_start, current_end = ordered[0]
    covered_length = 0
    for start, end in ordered[1:]:
        if start > current_end:
            covered_length += (
                current_end - current_start
            )
            current_start = start
            current_end = end
            continue
        current_end = max(
            current_end,
            end,
        )
    covered_length += current_end - current_start
    return covered_length


def analyze_tile_layout(
    request: TilingRequest,
) -> TileLayoutAnalysis:
    "Measure coverage and output cost for one tiling request"
    windows = generate_tile_windows(request)
    column_intervals = {
        (
            window.column_offset_pixels,
            window.read_width_pixels,
        )
        for window in windows
    }
    row_intervals = {
        (
            window.row_offset_pixels,
            window.read_height_pixels,
        )
        for window in windows
    }
    covered_width = _covered_axis_length(column_intervals)
    covered_height = _covered_axis_length(row_intervals)
    source_pixel_count = (request.grid.width * request.grid.height)
    covered_source_pixel_count = (covered_width * covered_height)
    total_read_pixel_count = sum(
        window.read_width_pixels
        * window.read_height_pixels
        for window in windows
    )
    total_output_pixel_count = (
        len(windows)
        * request.layout.tile_width_pixels
        * request.layout.tile_height_pixels
    )
    partial_tile_count = sum(
        window.is_partial
        for window in windows
    )

    return TileLayoutAnalysis(
        layout_id=build_tile_layout_id(
            request.layout
        ),
        tile_count=len(windows),
        full_tile_count=(
            len(windows) - partial_tile_count
        ),
        partial_tile_count=partial_tile_count,
        source_pixel_count=source_pixel_count,
        covered_source_pixel_count=(
            covered_source_pixel_count
        ),
        uncovered_source_pixel_count=(
            source_pixel_count
            - covered_source_pixel_count
        ),
        total_read_pixel_count=(
            total_read_pixel_count
        ),
        total_output_pixel_count=(
            total_output_pixel_count
        ),
        padded_output_pixel_count=(
            total_output_pixel_count
            - total_read_pixel_count
        ),
        repeated_read_pixel_count=(
            total_read_pixel_count
            - covered_source_pixel_count
        ),
    )