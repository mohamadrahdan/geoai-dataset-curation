import json
from dataclasses import replace
from pathlib import Path

import pytest

from geoai_dataset_curation.quality_control import (
    PairQCInputArtifacts,
    load_pair_qc_input_artifacts,
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    build_image_mask_pair_id,
    build_tile_negative_provenance_catalog_id,
    build_tile_sampling_selection_id,
    select_tile_candidates,
    write_image_mask_pair_catalog,
    write_tile_negative_provenance_catalog,
    write_tile_sampling_selection_catalog,
)
from geoai_dataset_curation.tiling import (
    TILE_CATALOG_SCHEMA_VERSION,
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    build_tile_catalog_id,
    write_tile_catalog,
)


GRID_ID = "sha256:" + ("a" * 64)
LAYOUT_ID = "sha256:" + ("b" * 64)
PLACEHOLDER_PAIR_ID = "sha256:" + ("0" * 64)
MODIFIED_ID = "sha256:" + ("f" * 64)


def make_candidate(
    *,
    digest_character: str,
    row_index: int,
    label_class: TileLabelClass,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 0, 15),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 15),
        TileLabelClass.ALL_IGNORE: (0, 0, 16),
    }
    positive, negative, ignore = counts[label_class]
    top = float(120 - (row_index * 40))
    return TileCandidateRecord(
        tile_id="sha256:" + (digest_character * 64),
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=row_index,
        column_index=0,
        row_offset_pixels=row_index * 4,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=0.0,
        bottom=top - 40.0,
        right=40.0,
        top=top,
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def make_input_artifacts():
    tile_catalog = TileCatalog(
        schema_version=TILE_CATALOG_SCHEMA_VERSION,
        output_name="quality-control-candidates",
        image_artifact_path="artifacts/source-image.tif",
        label_artifact_path="artifacts/source-label.tif",
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

    selection = select_tile_candidates(tile_catalog)

    provenance = TileNegativeProvenanceCatalog(
        schema_version=TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        ordinary_negative_source_id="ordinary-negative-source",
        hard_negative_source_id="hard-negative-source",
        records=(
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[0].tile_id,
                ordinary_negative_pixel_count=0,
                hard_negative_pixel_count=0,
                shared_negative_pixel_count=0,
            ),
            TileNegativeProvenance(
                tile_id=tile_catalog.tiles[1].tile_id,
                ordinary_negative_pixel_count=1,
                hard_negative_pixel_count=0,
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

    provenance_by_tile_id = {
        record.tile_id: record for record in provenance.records
    }
    pair_records = []

    for candidate in selection.selected_candidates:
        provenance_record = provenance_by_tile_id[candidate.tile_id]
        draft = ImageMaskPairRecord(
            pair_id=PLACEHOLDER_PAIR_ID,
            tile_id=candidate.tile_id,
            image_tile_path=f"pairs/images/{candidate.tile_id}.tif",
            mask_tile_path=f"pairs/masks/{candidate.tile_id}.tif",
            label_class=candidate.label_class,
            negative_provenance_kind=provenance_record.kind,
        )
        pair_records.append(
            replace(draft, pair_id=build_image_mask_pair_id(draft))
        )

    pair_catalog = ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="quality-control-pairs",
        tile_catalog_id=build_tile_catalog_id(tile_catalog),
        selection_id=build_tile_sampling_selection_id(
            selection,
            catalog=tile_catalog,
        ),
        provenance_catalog_id=build_tile_negative_provenance_catalog_id(
            provenance,
            catalog=tile_catalog,
        ),
        source_image_artifact_path=tile_catalog.image_artifact_path,
        source_label_artifact_path=tile_catalog.label_artifact_path,
        pairs=tuple(pair_records),
    )

    return tile_catalog, selection, provenance, pair_catalog


def write_input_artifacts(tmp_path: Path):
    tile_catalog, selection, provenance, pair_catalog = make_input_artifacts()

    paths = {
        "tile_catalog": tmp_path / "tile-catalog.json",
        "selection": tmp_path / "selection.json",
        "provenance": tmp_path / "negative-provenance.json",
        "pair_catalog": tmp_path / "pair-catalog.json",
    }

    write_tile_catalog(tile_catalog, paths["tile_catalog"])
    write_tile_sampling_selection_catalog(
        selection,
        catalog=tile_catalog,
        output_path=paths["selection"],
    )
    write_tile_negative_provenance_catalog(
        provenance,
        catalog=tile_catalog,
        output_path=paths["provenance"],
    )
    write_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        output_path=paths["pair_catalog"],
    )

    expected = PairQCInputArtifacts(
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
        pair_catalog=pair_catalog,
    )
    return expected, paths


def load_input_artifacts(paths: dict[str, Path]) -> PairQCInputArtifacts:
    return load_pair_qc_input_artifacts(
        tile_catalog_path=paths["tile_catalog"],
        selection_path=paths["selection"],
        provenance_path=paths["provenance"],
        pair_catalog_path=paths["pair_catalog"],
    )


def modify_json_field(path: Path, field_name: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[field_name] = MODIFIED_ID
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_pair_qc_inputs_round_trip_from_persisted_artifacts(
    tmp_path: Path,
) -> None:
    expected, paths = write_input_artifacts(tmp_path)

    loaded = load_input_artifacts(paths)

    assert loaded == expected
    assert loaded.tile_catalog.tile_count == 3
    assert loaded.selection.selected_tile_count == 2
    assert loaded.provenance.record_count == 3
    assert loaded.pair_catalog.pair_count == 2


@pytest.mark.parametrize(
    ("artifact_name", "identity_field"),
    [
        ("tile_catalog", "catalog_id"),
        ("selection", "selection_id"),
        ("provenance", "provenance_catalog_id"),
        ("pair_catalog", "pair_catalog_id"),
    ],
)
def test_modified_artifact_identity_is_rejected(
    tmp_path: Path,
    artifact_name: str,
    identity_field: str,
) -> None:
    _, paths = write_input_artifacts(tmp_path)
    modify_json_field(paths[artifact_name], identity_field)

    with pytest.raises(ValueError):
        load_input_artifacts(paths)