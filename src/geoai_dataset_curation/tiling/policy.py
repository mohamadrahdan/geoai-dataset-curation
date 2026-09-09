"Selected Loop 1 tiling policy"
from geoai_dataset_curation.tiling.contracts import (
    TileEdgePolicy,
    TileLayoutSpec,
)


LOOP1_TILING_LAYOUT = TileLayoutSpec(
    tile_width_pixels=256,
    tile_height_pixels=256,
    stride_x_pixels=192,
    stride_y_pixels=192,
    edge_policy=TileEdgePolicy.SHIFT_TO_FIT,
)