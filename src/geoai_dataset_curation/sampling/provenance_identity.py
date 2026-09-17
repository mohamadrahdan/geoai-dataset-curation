"Stable identity helpers for tile negative provenance"
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
)
from geoai_dataset_curation.sampling.provenance_validation import (
    validate_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.tiling.catalog import TileCatalog
from geoai_dataset_curation.tiling.identity import _build_sha256_id


def tile_negative_provenance_identity_payload(
    record: TileNegativeProvenance,
) -> dict[str, Any]:
    "Return the canonical identity payload for one provenance record"
    return {
        "tile_id": record.tile_id,
        "ordinary_negative_pixel_count": record.ordinary_negative_pixel_count,
        "hard_negative_pixel_count": record.hard_negative_pixel_count,
        "shared_negative_pixel_count": record.shared_negative_pixel_count,
    }


def tile_negative_provenance_catalog_identity_payload(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
) -> dict[str, Any]:
    "Return the canonical identity payload for one provenance catalog"
    errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=catalog,
    )
    if errors:
        raise ValueError(
            "Cannot identify invalid tile negative provenance: "
            + "; ".join(errors)
        )

    return {
        "schema_version": provenance.schema_version,
        "tile_catalog_id": provenance.tile_catalog_id,
        "ordinary_negative_source_id": provenance.ordinary_negative_source_id,
        "hard_negative_source_id": provenance.hard_negative_source_id,
        "records": [
            tile_negative_provenance_identity_payload(record)
            for record in provenance.records
        ],
    }


def build_tile_negative_provenance_catalog_id(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
) -> str:
    "Build a stable identifier for one provenance catalog"
    payload = tile_negative_provenance_catalog_identity_payload(
        provenance,
        catalog=catalog,
    )
    return _build_sha256_id(payload)