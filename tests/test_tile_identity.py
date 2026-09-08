from dataclasses import replace
import pytest
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLayoutSpec,
    build_tile_layout_id,
    build_tile_window_id,
    tile_layout_identity_payload,
    tile_window_identity_payload,
)


def make_layout() -> TileLayoutSpec:
    return TileLayoutSpec(
        tile_width_pixels=256,
        tile_height_pixels=256,
        stride_x_pixels=128,
        stride_y_pixels=128,
        edge_policy=TileEdgePolicy.PAD_PARTIAL,
    )


def build_example_tile_id(
    *,
    grid_id: str = "sha256:grid-a",
    row_index: int = 2,
    column_index: int = 3,
    row_offset: int = 256,
    column_offset: int = 384,
    read_width: int = 256,
    read_height: int = 256,
) -> str:
    return build_tile_window_id(
        grid_id=grid_id,
        layout=make_layout(),
        row_index=row_index,
        column_index=column_index,
        row_offset_pixels=row_offset,
        column_offset_pixels=column_offset,
        read_width_pixels=read_width,
        read_height_pixels=read_height,
    )


def test_tile_layout_identity_payload_is_complete() -> None:
    payload = tile_layout_identity_payload(
        make_layout()
    )
    assert payload == {
        "schema_version": "tile-layout-v1",
        "tile_width_pixels": 256,
        "tile_height_pixels": 256,
        "stride_x_pixels": 128,
        "stride_y_pixels": 128,
        "edge_policy": "pad_partial",
    }


def test_tile_layout_id_is_stable() -> None:
    first_id = build_tile_layout_id(make_layout())
    second_id = build_tile_layout_id(make_layout())
    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


@pytest.mark.parametrize(
    "changed_layout",
    [
        replace(
            make_layout(),
            tile_width_pixels=512,
        ),
        replace(
            make_layout(),
            stride_x_pixels=256,
        ),
        replace(
            make_layout(),
            edge_policy=TileEdgePolicy.DROP_PARTIAL,
        ),
    ],
)
def test_tile_layout_id_changes_with_layout(
    changed_layout: TileLayoutSpec,
) -> None:
    assert (
        build_tile_layout_id(make_layout())
        != build_tile_layout_id(changed_layout)
    )


def test_tile_window_identity_payload_links_grid_and_layout() -> None:
    layout = make_layout()
    payload = tile_window_identity_payload(
        grid_id="sha256:grid-a",
        layout=layout,
        row_index=2,
        column_index=3,
        row_offset_pixels=256,
        column_offset_pixels=384,
        read_width_pixels=256,
        read_height_pixels=256,
    )
    assert payload["schema_version"] == "tile-window-v1"
    assert payload["grid_id"] == "sha256:grid-a"
    assert payload["layout_id"] == build_tile_layout_id(layout)
    assert payload["row_index"] == 2
    assert payload["column_index"] == 3


def test_tile_window_id_is_stable() -> None:
    first_id = build_example_tile_id()
    second_id = build_example_tile_id()
    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_tile_window_id_changes_with_position() -> None:
    original_id = build_example_tile_id()
    moved_id = build_example_tile_id(
        row_index=3,
        row_offset=384,
    )
    assert original_id != moved_id


def test_tile_window_id_changes_with_grid() -> None:
    first_id = build_example_tile_id(
        grid_id="sha256:grid-a"
    )
    second_id = build_example_tile_id(
        grid_id="sha256:grid-b"
    )
    assert first_id != second_id


def test_tile_window_id_changes_for_partial_edge_window() -> None:
    full_id = build_example_tile_id()
    partial_id = build_example_tile_id(
        read_width=80,
        read_height=117,
    )
    assert full_id != partial_id