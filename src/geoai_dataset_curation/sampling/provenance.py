"Construction of tile-level negative-source provenance"
import numpy as np
from geoai_dataset_curation.sampling.contracts import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
)
from geoai_dataset_curation.sampling.provenance_validation import (
    validate_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCatalog,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


def _catalog_raster_shape(
    catalog: TileCatalog,
) -> tuple[int, int]:
    "Return the raster extent represented by the complete catalog"
    height = max(
        candidate.row_offset_pixels
        + candidate.read_height_pixels
        for candidate in catalog.tiles
    )
    width = max(
        candidate.column_offset_pixels
        + candidate.read_width_pixels
        for candidate in catalog.tiles
    )
    return height, width


def _validate_negative_source_masks(
    *,
    ordinary_negative_mask: np.ndarray,
    hard_negative_mask: np.ndarray,
    expected_shape: tuple[int, int],
) -> tuple[str, ...]:
    "Return validation errors for source-specific negative masks"
    errors: list[str] = []
    masks = (
        (
            "ordinary_negative_mask",
            ordinary_negative_mask,
        ),
        (
            "hard_negative_mask",
            hard_negative_mask,
        ),
    )

    for name, mask in masks:
        if not isinstance(mask, np.ndarray):
            errors.append(f"{name} must be a numpy array.")
            continue
        if mask.ndim != 2:
            errors.append(f"{name} must be two-dimensional.")
        if mask.dtype != np.dtype(np.bool_):
            errors.append(f"{name} must have boolean dtype.")

    if not all(
        isinstance(mask, np.ndarray)
        for _, mask in masks
    ):
        return tuple(errors)

    if ordinary_negative_mask.shape != hard_negative_mask.shape:
        errors.append("negative source masks must have identical shapes.")

    if ordinary_negative_mask.shape != expected_shape:
        errors.append(
            "negative source masks must match the candidate "
            "catalog raster extent."
        )
    return tuple(errors)


def build_tile_negative_provenance_catalog(
    catalog: TileCatalog,
    *,
    ordinary_negative_source_id: str,
    hard_negative_source_id: str,
    ordinary_negative_mask: np.ndarray,
    hard_negative_mask: np.ndarray,
) -> TileNegativeProvenanceCatalog:
    "Build source-specific negative provenance for every tile"
    catalog_errors = validate_tile_catalog(catalog)
    if catalog_errors:
        raise ValueError(
            "Cannot build provenance from an invalid tile catalog: "
            + "; ".join(catalog_errors)
        )

    mask_errors = _validate_negative_source_masks(
        ordinary_negative_mask=ordinary_negative_mask,
        hard_negative_mask=hard_negative_mask,
        expected_shape=_catalog_raster_shape(catalog),
    )
    if mask_errors:
        raise ValueError(
            "Cannot build tile negative provenance: "
            + "; ".join(mask_errors)
        )

    records: list[TileNegativeProvenance] = []
    for candidate in catalog.tiles:
        row_start = candidate.row_offset_pixels
        row_end = (
            row_start
            + candidate.read_height_pixels
        )
        column_start = candidate.column_offset_pixels
        column_end = (
            column_start
            + candidate.read_width_pixels
        )

        ordinary_tile_mask = ordinary_negative_mask[
            row_start:row_end,
            column_start:column_end,
        ]
        hard_tile_mask = hard_negative_mask[
            row_start:row_end,
            column_start:column_end,
        ]

        records.append(
            TileNegativeProvenance(
                tile_id=candidate.tile_id,
                ordinary_negative_pixel_count=int(
                    np.count_nonzero(
                        ordinary_tile_mask
                    )
                ),
                hard_negative_pixel_count=int(
                    np.count_nonzero(
                        hard_tile_mask
                    )
                ),
                shared_negative_pixel_count=int(
                    np.count_nonzero(
                        ordinary_tile_mask
                        & hard_tile_mask
                    )
                ),
            )
        )

    provenance = TileNegativeProvenanceCatalog(
        schema_version=(
            TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION
        ),
        tile_catalog_id=build_tile_catalog_id(catalog),
        ordinary_negative_source_id=(
            ordinary_negative_source_id
        ),
        hard_negative_source_id=(
            hard_negative_source_id
        ),
        records=tuple(records),
    )
    provenance_errors = (
        validate_tile_negative_provenance_catalog(
            provenance,
            catalog=catalog,
        )
    )
    if provenance_errors:
        raise ValueError(
            "Cannot produce invalid tile negative provenance: "
            + "; ".join(provenance_errors)
        )
    return provenance