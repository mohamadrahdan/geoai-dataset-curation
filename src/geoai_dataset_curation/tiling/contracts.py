"Contracts for deterministic raster tiling"
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from geoai_dataset_curation.image_construction.contracts import (
    RasterGridSpec,
)


class TileEdgePolicy(StrEnum):
    "Candidate behavior for incomplete raster-edge tiles"
    DROP_PARTIAL = "drop_partial"
    PAD_PARTIAL = "pad_partial"
    SHIFT_TO_FIT = "shift_to_fit"


@dataclass(frozen=True)
class TileLayoutSpec:
    "Spatial layout requested for candidate tile generation"
    tile_width_pixels: int
    tile_height_pixels: int
    stride_x_pixels: int
    stride_y_pixels: int
    edge_policy: TileEdgePolicy


@dataclass(frozen=True)
class TileWindowSpec:
    "One deterministic pixel window over the shared raster grid"
    tile_id: str
    row_index: int
    column_index: int
    row_offset_pixels: int
    column_offset_pixels: int
    read_width_pixels: int
    read_height_pixels: int
    output_width_pixels: int
    output_height_pixels: int

    @property
    def padding_right_pixels(self) -> int:
        "Return required padding beyond the source raster width"

        return (
            self.output_width_pixels
            - self.read_width_pixels
        )

    @property
    def padding_bottom_pixels(self) -> int:
        "Return required padding beyond the source raster height"
        return (
            self.output_height_pixels
            - self.read_height_pixels
        )

    @property
    def is_partial(self) -> bool:
        "Return whether the source window requires edge padding"
        return (
            self.padding_right_pixels > 0
            or self.padding_bottom_pixels > 0
        )


@dataclass(frozen=True)
class TilingRequest:
    "Input contract for tiling one aligned image-label raster pair"
    image_artifact_path: Path
    label_artifact_path: Path
    grid: RasterGridSpec
    grid_id: str
    layout: TileLayoutSpec
    output_name: str