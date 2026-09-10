from pathlib import Path
import numpy as np
import pytest
from geoai_dataset_curation.contracts import LabelValue
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling import (
    TileEdgePolicy,
    TileLabelClass,
    TileLayoutSpec,
    TilingRequest,
    build_tile_catalog,
    validate_tile_catalog,
)


def make_request(
    *,
    edge_policy: TileEdgePolicy = TileEdgePolicy.SHIFT_TO_FIT,
) -> TilingRequest:
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=6,
        height=5,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=100.0,
            d=0.0,
            e=-10.0,
            f=200.0,
        ),
    )
    return TilingRequest(
        image_artifact_path=Path("artifacts/image.tif"),
        label_artifact_path=Path("artifacts/labels.tif"),
        grid=grid,
        grid_id=build_raster_grid_id(grid),
        layout=TileLayoutSpec(
            tile_width_pixels=4,
            tile_height_pixels=4,
            stride_x_pixels=3,
            stride_y_pixels=3,
            edge_policy=edge_policy,
        ),
        output_name="candidate_tiles",
    )


def make_labels() -> np.ndarray:
    labels = np.full((5, 6), int(LabelValue.IGNORE), dtype=np.uint8)
    labels[0, 0] = int(LabelValue.POSITIVE)
    labels[4, 5] = int(LabelValue.NEGATIVE)
    return labels


def test_build_tile_catalog_creates_deterministic_records() -> None:
    request = make_request()
    labels = make_labels()
    first = build_tile_catalog(labels, request)
    second = build_tile_catalog(labels, request)
    assert first == second
    assert first.tile_count == 4
    assert validate_tile_catalog(first) == ()
    assert len({record.tile_id for record in first.tiles}) == 4
    assert tuple(
        (record.row_index, record.column_index)
        for record in first.tiles
    ) == ((0, 0), (0, 1), (1, 0), (1, 1))


def test_build_tile_catalog_preserves_bounds_and_label_classes() -> None:
    catalog = build_tile_catalog(make_labels(), make_request())
    assert (
        catalog.tiles[0].left,
        catalog.tiles[0].bottom,
        catalog.tiles[0].right,
        catalog.tiles[0].top,
    ) == (100.0, 160.0, 140.0, 200.0)
    assert (
        catalog.tiles[-1].left,
        catalog.tiles[-1].bottom,
        catalog.tiles[-1].right,
        catalog.tiles[-1].top,
    ) == (120.0, 150.0, 160.0, 190.0)
    assert tuple(record.label_class for record in catalog.tiles) == (
        TileLabelClass.POSITIVE,
        TileLabelClass.ALL_IGNORE,
        TileLabelClass.ALL_IGNORE,
        TileLabelClass.NEGATIVE_ONLY,
    )


def test_build_tile_catalog_counts_padding_as_ignore() -> None:
    request = make_request(edge_policy=TileEdgePolicy.PAD_PARTIAL)
    request = TilingRequest(
        image_artifact_path=request.image_artifact_path,
        label_artifact_path=request.label_artifact_path,
        grid=request.grid,
        grid_id=request.grid_id,
        layout=TileLayoutSpec(
            tile_width_pixels=4,
            tile_height_pixels=4,
            stride_x_pixels=4,
            stride_y_pixels=4,
            edge_policy=TileEdgePolicy.PAD_PARTIAL,
        ),
        output_name=request.output_name,
    )
    catalog = build_tile_catalog(make_labels(), request)
    final_record = catalog.tiles[-1]
    assert final_record.read_pixel_count == 2
    assert final_record.output_pixel_count == 16
    assert final_record.padding_pixel_count == 14
    assert final_record.ignore_pixel_count == 15
    assert final_record.ignore_pixel_count - final_record.padding_pixel_count == 1
    assert final_record.negative_pixel_count == 1


def test_build_tile_catalog_rejects_shape_mismatch() -> None:
    labels = np.full((4, 6), int(LabelValue.IGNORE), dtype=np.uint8)
    with pytest.raises(ValueError, match="shape"):
        build_tile_catalog(labels, make_request())


def test_build_tile_catalog_rejects_unknown_label_value() -> None:
    labels = make_labels()
    labels[2, 2] = 2
    with pytest.raises(ValueError, match="outside"):
        build_tile_catalog(labels, make_request())