from pathlib import Path
import numpy as np
from PIL import Image
import pytest
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.quality_control import (
    generate_pair_contact_sheets,
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
)
from geoai_dataset_curation.tiling import TileLabelClass


TRANSFORM = from_origin(
    0.0,
    40.0,
    10.0,
    10.0,
)
CRS = "EPSG:32639"


def write_pair(
    root: Path,
    *,
    digest_character: str,
) -> ImageMaskPairRecord:
    image_path = (
        root
        / "images"
        / f"{digest_character}.tif"
    )
    mask_path = (
        root
        / "masks"
        / f"{digest_character}.tif"
    )
    image_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    mask_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = np.arange(
        64,
        dtype=np.float64,
    ).reshape(4, 4, 4)
    mask = np.full(
        (4, 4),
        255,
        dtype=np.uint8,
    )
    mask[0, 0] = 1
    mask[0, 1] = 0

    with rasterio.open(
        image_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=4,
        dtype="float64",
        crs=CRS,
        transform=TRANSFORM,
    ) as dataset:
        dataset.write(image)

    with rasterio.open(
        mask_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=TRANSFORM,
        nodata=255,
    ) as dataset:
        dataset.write(mask, 1)

    return ImageMaskPairRecord(
        pair_id=(
            "sha256:"
            + digest_character * 64
        ),
        tile_id=(
            "sha256:"
            + digest_character * 64
        ),
        image_tile_path=image_path.as_posix(),
        mask_tile_path=mask_path.as_posix(),
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=(
            NegativeProvenanceKind.ORDINARY_NEGATIVE
        ),
    )


def make_catalog(
    tmp_path: Path,
) -> ImageMaskPairCatalog:
    pair_root = tmp_path / "pairs"

    return ImageMaskPairCatalog(
        schema_version=(
            IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION
        ),
        output_name="visual-review-pairs",
        tile_catalog_id="sha256:" + ("c" * 64),
        selection_id="sha256:" + ("d" * 64),
        provenance_catalog_id=(
            "sha256:" + ("e" * 64)
        ),
        source_image_artifact_path="source-image.tif",
        source_label_artifact_path="source-label.tif",
        pairs=(
            write_pair(
                pair_root,
                digest_character="a",
            ),
            write_pair(
                pair_root,
                digest_character="b",
            ),
        ),
    )


def test_contact_sheets_cover_every_pair(
    tmp_path: Path,
) -> None:
    catalog = make_catalog(tmp_path)
    output_directory = tmp_path / "review"

    page_paths = generate_pair_contact_sheets(
        catalog,
        output_directory=output_directory,
        tile_size=64,
        pairs_per_page=1,
    )
    assert len(page_paths) == 2
    assert all(
        path.is_file()
        for path in page_paths
    )
    with Image.open(page_paths[0]) as page:
        assert page.format == "PNG"
        assert page.width > 0
        assert page.height > 0


def test_contact_sheet_generation_is_deterministic(
    tmp_path: Path,
) -> None:
    catalog = make_catalog(tmp_path)

    first_paths = generate_pair_contact_sheets(
        catalog,
        output_directory=tmp_path / "first",
        tile_size=64,
        pairs_per_page=2,
    )
    second_paths = generate_pair_contact_sheets(
        catalog,
        output_directory=tmp_path / "second",
        tile_size=64,
        pairs_per_page=2,
    )
    assert len(first_paths) == 1
    assert len(second_paths) == 1
    assert (
        first_paths[0].read_bytes()
        == second_paths[0].read_bytes()
    )


def test_invalid_rgb_band_indices_are_rejected(
    tmp_path: Path,
) -> None:
    catalog = make_catalog(tmp_path)

    with pytest.raises(
        ValueError,
        match="exceed the image band count",
    ):
        generate_pair_contact_sheets(
            catalog,
            output_directory=tmp_path / "review",
            rgb_band_indices=(4, 3, 5),
            tile_size=64,
        )