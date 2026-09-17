from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.sampling import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    generate_image_mask_pairs,
    select_tile_candidates,
    verify_image_mask_pair_artifacts,
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
TRANSFORM = from_origin(0.0, 40.0, 10.0, 10.0)


def write_sources(
    tmp_path: Path,
) -> tuple[Path, Path]:
    image_path = tmp_path / "image.tif"
    label_path = tmp_path / "labels.tif"

    image = np.arange(
        16,
        dtype=np.float32,
    ).reshape(2, 4, 2)
    labels = np.full(
        (4, 2),
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
        height=4,
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
        height=4,
        count=1,
        dtype="uint8",
        crs="EPSG:32639",
        transform=TRANSFORM,
    ) as dataset:
        dataset.write(labels, 1)
    return image_path, label_path


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    label_class: TileLabelClass,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 0, 3),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 3),
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
        bottom=float(20 - row_index * 20),
        right=20.0,
        top=float(40 - row_index * 20),
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def make_context(tmp_path: Path):
    image_path, label_path = write_sources(tmp_path)
    tile_catalog = TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="verification-candidates",
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
        ),
    )
    selection = select_tile_candidates(tile_catalog)
    provenance = TileNegativeProvenanceCatalog(
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
        ),
    )
    pair_catalog = generate_image_mask_pairs(
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_root=tmp_path / "pairs",
        output_name="verification-pairs",
    )
    return tile_catalog, selection, provenance, pair_catalog


def test_verifier_accepts_valid_physical_pairs(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_context(tmp_path)
    )
    result = verify_image_mask_pair_artifacts(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert result.passes is True
    assert result.expected_pair_count == 2
    assert result.verified_pair_count == 2
    assert result.errors == ()


def test_verifier_rejects_missing_pair_artifact(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_context(tmp_path)
    )
    Path(pair_catalog.pairs[0].image_tile_path).unlink()
    result = verify_image_mask_pair_artifacts(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert result.passes is False
    assert (
        "pairs[0].image artifact does not exist."
        in result.errors
    )


def test_verifier_detects_changed_mask_pixels(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_context(tmp_path)
    )
    mask_path = Path(pair_catalog.pairs[0].mask_tile_path)

    with rasterio.open(mask_path, "r+") as dataset:
        data = dataset.read(1)
        data[0, 0] = 255
        dataset.write(data, 1)

    result = verify_image_mask_pair_artifacts(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert result.passes is False
    assert "pairs[0].mask pixels differ from source." in result.errors
    assert "pairs[0].positive count is unexpected." in result.errors


def test_verifier_detects_changed_transform(
    tmp_path: Path,
) -> None:
    tile_catalog, selection, provenance, pair_catalog = (
        make_context(tmp_path)
    )
    image_path = Path(pair_catalog.pairs[0].image_tile_path)
    with rasterio.open(image_path, "r+") as dataset:
        dataset.transform = from_origin(
            10.0,
            40.0,
            10.0,
            10.0,
        )

    result = verify_image_mask_pair_artifacts(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    assert result.passes is False
    assert "pairs[0].image transform is unexpected." in result.errors