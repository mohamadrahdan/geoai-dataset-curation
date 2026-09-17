from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.sampling import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    generate_image_mask_pairs,
    select_tile_candidates,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
TRANSFORM = from_origin(0.0, 60.0, 10.0, 10.0)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    label_class: TileLabelClass,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 0, 3),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 3),
        TileLabelClass.ALL_IGNORE: (0, 0, 4),
    }
    positive, negative, ignore = counts[label_class]
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 2,
        column_offset_pixels=0,
        read_width_pixels=2,
        read_height_pixels=2,
        output_width_pixels=2,
        output_height_pixels=2,
        left=0.0,
        bottom=40.0 - (row_index * 20.0),
        right=20.0,
        top=60.0 - (row_index * 20.0),
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def write_sources(
    tmp_path: Path,
    *,
    label_transform=TRANSFORM,
) -> tuple[Path, Path, np.ndarray, np.ndarray]:
    image_path = tmp_path / "image.tif"
    label_path = tmp_path / "labels.tif"

    image = np.arange(
        24,
        dtype=np.float32,
    ).reshape(2, 6, 2)

    labels = np.full(
        (6, 2),
        255,
        dtype=np.uint8,
    )
    labels[0, 0] = 1
    labels[2, 0] = 0
    with rasterio.open(
        image_path,
        "w",
        driver="GTiff",
        width=2,
        height=6,
        count=2,
        dtype="float32",
        crs="EPSG:32639",
        transform=TRANSFORM,
    ) as dataset:
        dataset.write(image)
    with rasterio.open(
        label_path,
        "w",
        driver="GTiff",
        width=2,
        height=6,
        count=1,
        dtype="uint8",
        crs="EPSG:32639",
        transform=label_transform,
    ) as dataset:
        dataset.write(labels, 1)
    return image_path, label_path, image, labels


def make_tile_catalog(
    image_path: Path,
    label_path: Path,
) -> TileCatalog:
    return TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="pair-generation-candidates",
        image_artifact_path=image_path.as_posix(),
        label_artifact_path=label_path.as_posix(),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        tiles=(
            make_candidate(
                digest_character="c",
                row_index=0,
                label_class=TileLabelClass.POSITIVE,
            ),
            make_candidate(
                digest_character="d",
                row_index=1,
                label_class=TileLabelClass.NEGATIVE_ONLY,
            ),
            make_candidate(
                digest_character="e",
                row_index=2,
                label_class=TileLabelClass.ALL_IGNORE,
            ),
        ),
    )


def make_provenance_catalog(
    tile_catalog: TileCatalog,
) -> TileNegativeProvenanceCatalog:
    return TileNegativeProvenanceCatalog(
        schema_version=TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        ordinary_negative_source_id="ordinary-negative",
        hard_negative_source_id="hard-negative",
        records=(
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[0].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[1].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=1,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[2].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
        ),
    )


def generate_test_pairs(tmp_path: Path):
    image_path, label_path, image, labels = write_sources(tmp_path)
    tile_catalog = make_tile_catalog(image_path, label_path)
    selection = select_tile_candidates(tile_catalog)
    provenance = make_provenance_catalog(tile_catalog)
    pair_catalog = generate_image_mask_pairs(
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_root=tmp_path / "pairs",
        output_name="test-image-mask-pairs",
    )
    return pair_catalog, image, labels


def test_generation_writes_only_selected_pairs(
    tmp_path: Path,
) -> None:
    pair_catalog, _, _ = generate_test_pairs(tmp_path)
    assert pair_catalog.pair_count == 2
    assert pair_catalog.positive_pair_count == 1
    assert pair_catalog.negative_only_pair_count == 1
    for pair in pair_catalog.pairs:
        assert Path(pair.image_tile_path).is_file()
        assert Path(pair.mask_tile_path).is_file()


def test_generation_preserves_source_pixel_values(
    tmp_path: Path,
) -> None:
    pair_catalog, image, labels = generate_test_pairs(tmp_path)

    with rasterio.open(
        pair_catalog.pairs[0].image_tile_path
    ) as image_tile:
        assert np.array_equal(
            image_tile.read(),
            image[:, 0:2, :],
        )
    with rasterio.open(
        pair_catalog.pairs[1].mask_tile_path
    ) as mask_tile:
        assert np.array_equal(
            mask_tile.read(1),
            labels[2:4, :],
        )


def test_generation_preserves_tile_georeferencing(
    tmp_path: Path,
) -> None:
    pair_catalog, _, _ = generate_test_pairs(tmp_path)
    with rasterio.open(
        pair_catalog.pairs[1].image_tile_path
    ) as image_tile:
        assert image_tile.crs.to_string() == "EPSG:32639"
        assert image_tile.width == 2
        assert image_tile.height == 2
        assert image_tile.count == 2
        assert image_tile.dtypes == ("float32", "float32")
        assert image_tile.transform == from_origin(
            0.0,
            40.0,
            10.0,
            10.0,
        )

    with rasterio.open(
        pair_catalog.pairs[1].mask_tile_path
    ) as mask_tile:
        assert mask_tile.crs.to_string() == "EPSG:32639"
        assert mask_tile.width == 2
        assert mask_tile.height == 2
        assert mask_tile.count == 1
        assert mask_tile.dtypes == ("uint8",)
        assert mask_tile.nodata == 255


def test_repeated_generation_is_deterministic(
    tmp_path: Path,
) -> None:
    first, _, _ = generate_test_pairs(tmp_path)
    second, _, _ = generate_test_pairs(tmp_path)
    assert first == second


def test_generation_rejects_misaligned_sources(
    tmp_path: Path,
) -> None:
    image_path, label_path, _, _ = write_sources(
        tmp_path,
        label_transform=from_origin(
            10.0,
            60.0,
            10.0,
            10.0,
        ),
    )
    tile_catalog = make_tile_catalog(image_path, label_path)
    selection = select_tile_candidates(tile_catalog)
    provenance = make_provenance_catalog(tile_catalog)
    with pytest.raises(
        ValueError,
        match="Source image and label transforms must match",
    ):
        generate_image_mask_pairs(
            tile_catalog=tile_catalog,
            selection=selection,
            provenance=provenance,
            output_root=tmp_path / "pairs",
            output_name="test-image-mask-pairs",
        )