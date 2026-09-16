from dataclasses import FrozenInstanceError
import pytest
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
)
from geoai_dataset_curation.tiling import TileLabelClass


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)
TILE_CATALOG_ID = "sha256:" + ("c" * 64)
SELECTION_ID = "sha256:" + ("d" * 64)
PROVENANCE_CATALOG_ID = "sha256:" + ("e" * 64)


def make_pair(
    *,
    pair_id: str,
    tile_id: str,
    label_class: TileLabelClass,
    provenance_kind: NegativeProvenanceKind,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=pair_id,
        tile_id=tile_id,
        image_tile_path=f"pairs/images/{tile_id}.tif",
        mask_tile_path=f"pairs/masks/{tile_id}.tif",
        label_class=label_class,
        negative_provenance_kind=provenance_kind,
    )


def test_image_mask_pair_record_preserves_contract_fields() -> None:
    pair = make_pair(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        label_class=TileLabelClass.POSITIVE,
        provenance_kind=NegativeProvenanceKind.MIXED_NEGATIVE,
    )
    assert pair.pair_id == PAIR_ID
    assert pair.tile_id == TILE_ID
    assert pair.image_tile_path == f"pairs/images/{TILE_ID}.tif"
    assert pair.mask_tile_path == f"pairs/masks/{TILE_ID}.tif"
    assert pair.label_class == TileLabelClass.POSITIVE
    assert (
        pair.negative_provenance_kind
        == NegativeProvenanceKind.MIXED_NEGATIVE
    )


def test_image_mask_pair_catalog_reports_pair_counts() -> None:
    positive = make_pair(
        pair_id="sha256:" + ("f" * 64),
        tile_id="sha256:" + ("1" * 64),
        label_class=TileLabelClass.POSITIVE,
        provenance_kind=NegativeProvenanceKind.NONE,
    )
    negative = make_pair(
        pair_id="sha256:" + ("0" * 64),
        tile_id="sha256:" + ("2" * 64),
        label_class=TileLabelClass.NEGATIVE_ONLY,
        provenance_kind=NegativeProvenanceKind.HARD_NEGATIVE,
    )

    catalog = ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="loop1-image-mask-pairs",
        tile_catalog_id=TILE_CATALOG_ID,
        selection_id=SELECTION_ID,
        provenance_catalog_id=PROVENANCE_CATALOG_ID,
        source_image_artifact_path="artifacts/image.tif",
        source_label_artifact_path="artifacts/labels.tif",
        pairs=(positive, negative),
    )
    assert catalog.pair_count == 2
    assert catalog.positive_pair_count == 1
    assert catalog.negative_only_pair_count == 1


def test_pair_contracts_are_immutable() -> None:
    pair = make_pair(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        label_class=TileLabelClass.POSITIVE,
        provenance_kind=NegativeProvenanceKind.NONE,
    )
    with pytest.raises(FrozenInstanceError):
        pair.tile_id = "changed"  # type: ignore[misc]