"Physical verification of generated image-mask pair artifacts"
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from rasterio.windows import Window
from geoai_dataset_curation.sampling.contracts import (
    ImageMaskPairCatalog,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.pair_validation import (
    validate_image_mask_pair_catalog,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCatalog,
    TileLabelClass,
)


ALLOWED_MASK_VALUES = {0, 1, 255}


@dataclass(frozen=True)
class ImageMaskPairArtifactVerification:
    "Summary of physical image-mask pair verification"
    expected_pair_count: int
    verified_pair_count: int
    errors: tuple[str, ...]

    @property
    def passes(self) -> bool:
        "Return whether every expected pair passed verification"
        return (
            not self.errors
            and self.verified_pair_count == self.expected_pair_count
        )


def _expected_tile_arrays(
    *,
    candidate,
    image_source,
    label_source,
) -> tuple[np.ndarray, np.ndarray, Window]:
    "Return expected output arrays and source window for one tile"
    row_start = candidate.row_offset_pixels
    row_end = row_start + candidate.read_height_pixels
    column_start = candidate.column_offset_pixels
    column_end = column_start + candidate.read_width_pixels

    window = Window.from_slices(
        rows=(row_start, row_end),
        cols=(column_start, column_end),
    )

    source_image = image_source.read(window=window)
    source_mask = label_source.read(1, window=window)

    image_fill_value = (
        image_source.nodata
        if image_source.nodata is not None
        else 0
    )
    expected_image = np.full(
        (
            image_source.count,
            candidate.output_height_pixels,
            candidate.output_width_pixels,
        ),
        image_fill_value,
        dtype=source_image.dtype,
    )
    expected_mask = np.full(
        (
            candidate.output_height_pixels,
            candidate.output_width_pixels,
        ),
        255,
        dtype=np.uint8,
    )
    expected_image[
        :,
        :candidate.read_height_pixels,
        :candidate.read_width_pixels,
    ] = source_image
    expected_mask[
        :candidate.read_height_pixels,
        :candidate.read_width_pixels,
    ] = source_mask
    return expected_image, expected_mask, window


def verify_image_mask_pair_artifacts(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
) -> ImageMaskPairArtifactVerification:
    "Verify every physical image-mask pair against source evidence"
    catalog_errors = validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )
    if catalog_errors:
        return ImageMaskPairArtifactVerification(
            expected_pair_count=pair_catalog.pair_count,
            verified_pair_count=0,
            errors=tuple(
                f"catalog.{error}"
                for error in catalog_errors
            ),
        )

    errors: list[str] = []
    verified_pair_count = 0
    image_source_path = Path(
        pair_catalog.source_image_artifact_path
    )
    label_source_path = Path(pair_catalog.source_label_artifact_path)

    if not image_source_path.is_file():
        errors.append("source image artifact does not exist.")

    if not label_source_path.is_file():
        errors.append("source label artifact does not exist.")

    if errors:
        return ImageMaskPairArtifactVerification(
            expected_pair_count=pair_catalog.pair_count,
            verified_pair_count=0,
            errors=tuple(errors),
        )

    candidates_by_id = {
        candidate.tile_id: candidate
        for candidate in selection.selected_candidates
    }

    with rasterio.open(image_source_path) as image_source:
        with rasterio.open(label_source_path) as label_source:
            for index, pair in enumerate(pair_catalog.pairs):
                pair_error_count = len(errors)
                candidate = candidates_by_id[pair.tile_id]
                image_path = Path(pair.image_tile_path)
                mask_path = Path(pair.mask_tile_path)

                if not image_path.is_file():
                    errors.append(f"pairs[{index}].image artifact does not exist.")

                if not mask_path.is_file():
                    errors.append(f"pairs[{index}].mask artifact does not exist.")

                if not image_path.is_file() or not mask_path.is_file():
                    continue

                try:
                    image_tile = rasterio.open(image_path)
                    mask_tile = rasterio.open(mask_path)
                except RasterioIOError:
                    errors.append(
                        f"pairs[{index}].artifacts must be readable GeoTIFFs."
                    )
                    continue

                with image_tile, mask_tile:
                    expected_image, expected_mask, window = (
                        _expected_tile_arrays(
                            candidate=candidate,
                            image_source=image_source,
                            label_source=label_source,
                        )
                    )
                    expected_transform = (
                        image_source.window_transform(window)
                    )

                    if image_tile.width != candidate.output_width_pixels:
                        errors.append(
                            f"pairs[{index}].image width is unexpected."
                        )

                    if image_tile.height != candidate.output_height_pixels:
                        errors.append(
                            f"pairs[{index}].image height is unexpected."
                        )

                    if mask_tile.width != candidate.output_width_pixels:
                        errors.append(
                            f"pairs[{index}].mask width is unexpected."
                        )

                    if mask_tile.height != candidate.output_height_pixels:
                        errors.append(
                            f"pairs[{index}].mask height is unexpected."
                        )

                    if image_tile.count != image_source.count:
                        errors.append(
                            f"pairs[{index}].image band count is unexpected."
                        )

                    if image_tile.dtypes != image_source.dtypes:
                        errors.append(
                            f"pairs[{index}].image dtypes are unexpected."
                        )

                    if mask_tile.count != 1:
                        errors.append(
                            f"pairs[{index}].mask must contain one band."
                        )

                    if mask_tile.dtypes != ("uint8",):
                        errors.append(f"pairs[{index}].mask dtype must be uint8.")

                    if mask_tile.nodata != 255:
                        errors.append(f"pairs[{index}].mask nodata must be 255.")

                    if image_tile.crs != image_source.crs:
                        errors.append(f"pairs[{index}].image CRS is unexpected.")

                    if mask_tile.crs != label_source.crs:
                        errors.append(f"pairs[{index}].mask CRS is unexpected.")

                    if image_tile.crs != mask_tile.crs:
                        errors.append(f"pairs[{index}].image and mask CRS values differ.")

                    if image_tile.transform != expected_transform:
                        errors.append(f"pairs[{index}].image transform is unexpected.")

                    if mask_tile.transform != expected_transform:
                        errors.append(f"pairs[{index}].mask transform is unexpected.")

                    observed_image = image_tile.read()
                    observed_mask = mask_tile.read(1)

                    if not np.array_equal(
                        observed_image,
                        expected_image,
                        equal_nan=True,
                    ):
                        errors.append(f"pairs[{index}].image pixels differ from source.")

                    if not np.array_equal(
                        observed_mask,
                        expected_mask,
                    ):
                        errors.append(f"pairs[{index}].mask pixels differ from source.")

                    observed_values = {
                        int(value)
                        for value in np.unique(observed_mask)
                    }
                    if not observed_values.issubset(ALLOWED_MASK_VALUES):
                        errors.append(f"pairs[{index}].mask contains unsupported values.")

                    positive_count = int(np.count_nonzero(observed_mask == 1))
                    negative_count = int(np.count_nonzero(observed_mask == 0))
                    ignore_count = int(np.count_nonzero(observed_mask == 255))

                    if positive_count != candidate.positive_pixel_count:
                        errors.append(f"pairs[{index}].positive count is unexpected.")

                    if negative_count != candidate.negative_pixel_count:
                        errors.append(f"pairs[{index}].negative count is unexpected.")

                    if ignore_count != candidate.ignore_pixel_count:
                        errors.append(f"pairs[{index}].ignore count is unexpected.")

                    if pair.label_class == TileLabelClass.ALL_IGNORE:
                        errors.append(f"pairs[{index}].all-ignore pair is forbidden.")
                if len(errors) == pair_error_count:
                    verified_pair_count += 1
    return ImageMaskPairArtifactVerification(
        expected_pair_count=pair_catalog.pair_count,
        verified_pair_count=verified_pair_count,
        errors=tuple(errors),
    )