from dataclasses import replace
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    build_image_mask_pair_catalog_id,
    build_image_mask_pair_id,
    image_mask_pair_catalog_identity_payload,
    image_mask_pair_identity_payload,
)
from geoai_dataset_curation.tiling import TileLabelClass


PLACEHOLDER_PAIR_ID = "sha256:" + ("0" * 64)
TILE_ID = "sha256:" + ("a" * 64)
TILE_CATALOG_ID = "sha256:" + ("b" * 64)
SELECTION_ID = "sha256:" + ("c" * 64)
PROVENANCE_CATALOG_ID = "sha256:" + ("d" * 64)


def make_pair() -> ImageMaskPairRecord:
    draft = ImageMaskPairRecord(
        pair_id=PLACEHOLDER_PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path="pairs/images/tile-a.tif",
        mask_tile_path="pairs/masks/tile-a.tif",
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=NegativeProvenanceKind.NONE,
    )
    return replace(draft, pair_id=build_image_mask_pair_id(draft),)


def make_pair_catalog() -> ImageMaskPairCatalog:
    return ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="loop1-image-mask-pairs",
        tile_catalog_id=TILE_CATALOG_ID,
        selection_id=SELECTION_ID,
        provenance_catalog_id=PROVENANCE_CATALOG_ID,
        source_image_artifact_path="artifacts/image.tif",
        source_label_artifact_path="artifacts/labels.tif",
        pairs=(make_pair(),),
    )


def test_pair_identity_payload_contains_semantic_fields() -> None:
    pair = make_pair()
    assert image_mask_pair_identity_payload(pair) == {
        "tile_id": TILE_ID,
        "image_tile_path": "pairs/images/tile-a.tif",
        "mask_tile_path": "pairs/masks/tile-a.tif",
        "label_class": "positive",
        "negative_provenance_kind": "none",
    }


def test_pair_identity_is_stable() -> None:
    pair = make_pair()
    first_id = build_image_mask_pair_id(pair)
    second_id = build_image_mask_pair_id(pair)
    assert first_id == second_id
    assert first_id == pair.pair_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71


def test_pair_identity_changes_with_output_path() -> None:
    pair = make_pair()
    changed = replace(
        pair,
        image_tile_path="pairs/images/changed.tif",
    )
    assert build_image_mask_pair_id(pair) != build_image_mask_pair_id(changed)


def test_pair_catalog_identity_is_stable() -> None:
    catalog = make_pair_catalog()
    payload = image_mask_pair_catalog_identity_payload(catalog)
    first_id = build_image_mask_pair_catalog_id(catalog)
    second_id = build_image_mask_pair_catalog_id(catalog)
    assert payload["pairs"][0]["pair_id"] == catalog.pairs[0].pair_id
    assert first_id == second_id
    assert first_id.startswith("sha256:")
    assert len(first_id) == 71