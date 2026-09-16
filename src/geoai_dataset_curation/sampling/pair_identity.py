"Stable identity helpers for image-mask pair catalogs"
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
)
from geoai_dataset_curation.tiling.identity import _build_sha256_id


def image_mask_pair_identity_payload(
    pair: ImageMaskPairRecord,
) -> dict[str, Any]:
    "Return the canonical identity payload for one image-mask pair"
    return {
        "tile_id": pair.tile_id,
        "image_tile_path": pair.image_tile_path,
        "mask_tile_path": pair.mask_tile_path,
        "label_class": pair.label_class.value,
        "negative_provenance_kind": pair.negative_provenance_kind.value,
    }


def build_image_mask_pair_id(
    pair: ImageMaskPairRecord,
) -> str:
    "Build a stable identifier for one image-mask pair"
    return _build_sha256_id(image_mask_pair_identity_payload(pair))


def image_mask_pair_catalog_identity_payload(
    catalog: ImageMaskPairCatalog,
) -> dict[str, Any]:
    "Return the canonical identity payload for one pair catalog"
    return {
        "schema_version": catalog.schema_version,
        "output_name": catalog.output_name,
        "tile_catalog_id": catalog.tile_catalog_id,
        "selection_id": catalog.selection_id,
        "provenance_catalog_id": catalog.provenance_catalog_id,
        "source_image_artifact_path": (catalog.source_image_artifact_path),
        "source_label_artifact_path": (catalog.source_label_artifact_path),
        "pairs": [{
                "pair_id": pair.pair_id,
                **image_mask_pair_identity_payload(pair),
            }
            for pair in catalog.pairs
        ],
    }


def build_image_mask_pair_catalog_id(
    catalog: ImageMaskPairCatalog,
) -> str:
    "Build a stable identifier for one complete pair catalog"
    return _build_sha256_id(image_mask_pair_catalog_identity_payload(catalog))