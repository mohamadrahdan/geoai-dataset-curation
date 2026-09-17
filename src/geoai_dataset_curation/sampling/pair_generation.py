"Physical generation of selected image-mask GeoTIFF pairs"

from dataclasses import replace
from pathlib import Path

from affine import Affine
import numpy as np
import rasterio
from rasterio.io import DatasetReader
from rasterio.windows import Window

from geoai_dataset_curation.sampling.contracts import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.pair_identity import (
    build_image_mask_pair_id,
)
from geoai_dataset_curation.sampling.pair_validation import (
    validate_image_mask_pair_catalog,
)
from geoai_dataset_curation.sampling.provenance_identity import (
    build_tile_negative_provenance_catalog_id,
)
from geoai_dataset_curation.sampling.provenance_validation import (
    validate_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.sampling.selection_identity import (
    build_tile_sampling_selection_id,
)
from geoai_dataset_curation.sampling.selection_validation import (
    validate_tile_sampling_selection,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


PLACEHOLDER_PAIR_ID = "sha256:" + ("0" * 64)
ALLOWED_MASK_VALUES = {0, 1, 255}


def _validate_source_rasters(
    image_dataset: DatasetReader,
    label_dataset: DatasetReader,
) -> None:
    "Raise when source image and label rasters are not aligned"
    if image_dataset.crs != label_dataset.crs:
        raise ValueError("Source image and label CRS values must match.")

    if image_dataset.width != label_dataset.width:
        raise ValueError("Source image and label widths must match.")

    if image_dataset.height != label_dataset.height:
        raise ValueError("Source image and label heights must match.")

    if image_dataset.transform != label_dataset.transform:
        raise ValueError("Source image and label transforms must match.")

    if label_dataset.count != 1:
        raise ValueError("Source label raster must contain exactly one band.")

    if label_dataset.dtypes != ("uint8",):
        raise ValueError("Source label raster must use uint8 dtype.")


def _read_candidate_arrays(
    *,
    candidate: TileCandidateRecord,
    image_dataset: DatasetReader,
    label_dataset: DatasetReader,
) -> tuple[np.ndarray, np.ndarray, Affine]:
    "Read and pad one selected image-mask window"
    row_start = candidate.row_offset_pixels
    row_end = row_start + candidate.read_height_pixels
    column_start = candidate.column_offset_pixels
    column_end = column_start + candidate.read_width_pixels

    window = Window.from_slices(
        rows=(row_start, row_end),
        cols=(column_start, column_end),
    )

    image_source = image_dataset.read(window=window)
    mask_source = label_dataset.read(1, window=window)

    image_fill_value = (
        image_dataset.nodata
        if image_dataset.nodata is not None
        else 0
    )

    image_tile = np.full(
        (
            image_dataset.count,
            candidate.output_height_pixels,
            candidate.output_width_pixels,
        ),
        image_fill_value,
        dtype=image_source.dtype,
    )

    mask_tile = np.full(
        (
            candidate.output_height_pixels,
            candidate.output_width_pixels,
        ),
        255,
        dtype=np.uint8,
    )

    image_tile[
        :,
        :candidate.read_height_pixels,
        :candidate.read_width_pixels,
    ] = image_source

    mask_tile[
        :candidate.read_height_pixels,
        :candidate.read_width_pixels,
    ] = mask_source

    observed_values = {
        int(value)
        for value in np.unique(mask_tile)
    }

    if not observed_values.issubset(ALLOWED_MASK_VALUES):
        raise ValueError("Generated mask contains unsupported label values.")

    positive_count = int(
        np.count_nonzero(mask_tile == 1)
    )
    negative_count = int(
        np.count_nonzero(mask_tile == 0)
    )
    ignore_count = int(
        np.count_nonzero(mask_tile == 255)
    )

    if positive_count != candidate.positive_pixel_count:
        raise ValueError("Generated positive pixel count is unexpected.")

    if negative_count != candidate.negative_pixel_count:
        raise ValueError("Generated negative pixel count is unexpected.")

    if ignore_count != candidate.ignore_pixel_count:
        raise ValueError("Generated ignore pixel count is unexpected.")

    transform = image_dataset.window_transform(window)
    return image_tile, mask_tile, transform


def _write_pair_artifacts(
    *,
    image_tile: np.ndarray,
    mask_tile: np.ndarray,
    transform: Affine,
    image_dataset: DatasetReader,
    label_dataset: DatasetReader,
    image_path: Path,
    mask_path: Path,
) -> None:
    "Write one aligned image-mask pair as compressed GeoTIFFs"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)

    image_profile = image_dataset.profile.copy()
    image_profile.update(
        driver="GTiff",
        width=image_tile.shape[2],
        height=image_tile.shape[1],
        count=image_tile.shape[0],
        dtype=str(image_tile.dtype),
        transform=transform,
        compress="deflate",
    )

    mask_profile = label_dataset.profile.copy()
    mask_profile.update(
        driver="GTiff",
        width=mask_tile.shape[1],
        height=mask_tile.shape[0],
        count=1,
        dtype="uint8",
        transform=transform,
        nodata=255,
        compress="deflate",
    )

    with rasterio.open(
        image_path,
        "w",
        **image_profile,
    ) as dataset:
        dataset.write(image_tile)

    with rasterio.open(
        mask_path,
        "w",
        **mask_profile,
    ) as dataset:
        dataset.write(mask_tile, 1)


def generate_image_mask_pairs(
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
    output_root: Path,
    output_name: str,
) -> ImageMaskPairCatalog:
    "Generate every selected image-mask pair and its catalog"
    tile_catalog_errors = validate_tile_catalog(tile_catalog)
    if tile_catalog_errors:
        raise ValueError(
            "Cannot generate pairs from an invalid tile catalog: "
            + "; ".join(tile_catalog_errors)
        )

    selection_errors = validate_tile_sampling_selection(
        selection,
        catalog=tile_catalog,
    )
    if selection_errors:
        raise ValueError(
            "Cannot generate pairs from an invalid selection: "
            + "; ".join(selection_errors)
        )

    provenance_errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=tile_catalog,
    )
    if provenance_errors:
        raise ValueError(
            "Cannot generate pairs from invalid provenance: "
            + "; ".join(provenance_errors)
        )

    if not output_name.strip():
        raise ValueError("Pair output_name must not be empty.")

    image_source_path = Path(
        tile_catalog.image_artifact_path
    )
    label_source_path = Path(
        tile_catalog.label_artifact_path
    )

    if not image_source_path.is_file():
        raise FileNotFoundError(
            f"Source image artifact not found: {image_source_path}"
        )

    if not label_source_path.is_file():
        raise FileNotFoundError(
            f"Source label artifact not found: {label_source_path}"
        )

    provenance_by_id = {
        record.tile_id: record
        for record in provenance.records
    }

    pairs: list[ImageMaskPairRecord] = []
    image_output_directory = output_root / "images"
    mask_output_directory = output_root / "masks"

    with rasterio.open(image_source_path) as image_dataset:
        with rasterio.open(label_source_path) as label_dataset:
            _validate_source_rasters(
                image_dataset,
                label_dataset,
            )

            for candidate in selection.selected_candidates:
                provenance_record = provenance_by_id[
                    candidate.tile_id
                ]
                tile_digest = candidate.tile_id.removeprefix(
                    "sha256:"
                )
                image_path = (
                    image_output_directory
                    / f"{tile_digest}.tif"
                )
                mask_path = (
                    mask_output_directory
                    / f"{tile_digest}.tif"
                )

                image_tile, mask_tile, transform = (
                    _read_candidate_arrays(
                        candidate=candidate,
                        image_dataset=image_dataset,
                        label_dataset=label_dataset,
                    )
                )

                _write_pair_artifacts(
                    image_tile=image_tile,
                    mask_tile=mask_tile,
                    transform=transform,
                    image_dataset=image_dataset,
                    label_dataset=label_dataset,
                    image_path=image_path,
                    mask_path=mask_path,
                )

                draft = ImageMaskPairRecord(
                    pair_id=PLACEHOLDER_PAIR_ID,
                    tile_id=candidate.tile_id,
                    image_tile_path=image_path.as_posix(),
                    mask_tile_path=mask_path.as_posix(),
                    label_class=candidate.label_class,
                    negative_provenance_kind=provenance_record.kind,
                )

                pairs.append(
                    replace(
                        draft,
                        pair_id=build_image_mask_pair_id(draft),
                    )
                )

    pair_catalog = ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name=output_name,
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        selection_id=build_tile_sampling_selection_id(
            selection,
            catalog=tile_catalog,
        ),
        provenance_catalog_id=(
            build_tile_negative_provenance_catalog_id(
                provenance,
                catalog=tile_catalog,
            )
        ),
        source_image_artifact_path=(
            tile_catalog.image_artifact_path
        ),
        source_label_artifact_path=(
            tile_catalog.label_artifact_path
        ),
        pairs=tuple(pairs),
    )

    pair_catalog_errors = validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    if pair_catalog_errors:
        raise ValueError(
            "Cannot produce an invalid image-mask pair catalog: "
            + "; ".join(pair_catalog_errors)
        )

    return pair_catalog