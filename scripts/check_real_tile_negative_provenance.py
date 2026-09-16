"Build and verify real Loop 1 tile-level negative provenance"
from collections import Counter
from pathlib import Path
import numpy as np
import rasterio
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.label_rasterization import (
    load_real_reference_source_configs,
    wire_real_reference_sources,
)
from geoai_dataset_curation.sampling import (
    LOOP1_SAMPLING_POLICY,
    NegativeProvenanceKind,
    build_tile_negative_provenance_catalog,
    build_tile_negative_provenance_catalog_id,
    build_tile_sampling_selection_id,
    rasterize_negative_source_mask,
    select_tile_candidates,
    verify_tile_negative_provenance_artifact,
    verify_tile_sampling_selection_artifact,
    write_tile_negative_provenance_catalog,
    write_tile_sampling_selection_catalog,
)
from geoai_dataset_curation.tiling import (
    LOOP1_TILING_LAYOUT,
    TileLabelClass,
    TilingRequest,
    build_tile_catalog,
    build_tile_catalog_id,
    verify_tile_catalog_artifact,
)


IMAGE_PATH = Path("artifacts/live/loop1/komeh_sentinel2_2024_median.tif")
LABEL_PATH = Path("artifacts/live/loop1/komeh_labels_v1.tif")
CATALOG_PATH = Path("artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json")
PROVENANCE_PATH = Path("artifacts/live/loop1/komeh_tile_negative_provenance_v1.catalog.json")
SELECTION_PATH = Path("artifacts/live/loop1/komeh_sampling_selection_v1.catalog.json")
EXPECTED_GRID_ID = (
    "sha256:"
    "d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799"
)
EXPECTED_CATALOG_ID = (
    "sha256:"
    "3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28"
)
EXPECTED_PROVENANCE_CATALOG_ID = (
    "sha256:"
    "1cd474b5a004e0ac3f6cc0e7fd8649ae4eee5acd3e6e651491eeec90163263d1"
)
EXPECTED_SELECTION_ID = (
    "sha256:"
    "3b455b9e8616322378c44e0e373381b11b3c95db3dd80426ff243e095ed9ec6b"
)

EXPECTED_TILE_COUNT = 870
EXPECTED_PROVENANCE_RECORD_COUNT = 870
EXPECTED_SELECTED_TILE_COUNT = 50
EXPECTED_POSITIVE_TILE_COUNT = 19
EXPECTED_NEGATIVE_ONLY_TILE_COUNT = 31
EXPECTED_ALL_IGNORE_TILE_COUNT = 820

EXPECTED_ORDINARY_NEGATIVE_FEATURE_COUNT = 54
EXPECTED_HARD_NEGATIVE_FEATURE_COUNT = 49
EXPECTED_ORDINARY_NEGATIVE_PIXEL_COUNT = 23_640
EXPECTED_HARD_NEGATIVE_PIXEL_COUNT = 40_751
EXPECTED_SHARED_NEGATIVE_PIXEL_COUNT = 3
EXPECTED_UNION_NEGATIVE_PIXEL_COUNT = 64_388

EXPECTED_ALL_PROVENANCE_KIND_COUNTS = {
    NegativeProvenanceKind.NONE: 826,
    NegativeProvenanceKind.ORDINARY_NEGATIVE: 10,
    NegativeProvenanceKind.HARD_NEGATIVE: 21,
    NegativeProvenanceKind.MIXED_NEGATIVE: 13,
}

EXPECTED_SELECTED_PROVENANCE_KIND_COUNTS = {
    NegativeProvenanceKind.NONE: 6,
    NegativeProvenanceKind.ORDINARY_NEGATIVE: 10,
    NegativeProvenanceKind.HARD_NEGATIVE: 21,
    NegativeProvenanceKind.MIXED_NEGATIVE: 13,
}

EXPECTED_TILE_NEGATIVE_OBSERVATION_COUNT = 116_695


def main() -> None:
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"Image artifact not found: {IMAGE_PATH}")
    if not LABEL_PATH.is_file():
        raise FileNotFoundError(f"Label artifact not found: {LABEL_PATH}")
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError(f"Candidate catalog artifact not found: {CATALOG_PATH}")
    with rasterio.open(IMAGE_PATH) as image_dataset:
        with rasterio.open(LABEL_PATH) as label_dataset:
            if image_dataset.crs != label_dataset.crs:
                raise RuntimeError("Image and label CRS values do not match.")
            if image_dataset.width != label_dataset.width:
                raise RuntimeError("Image and label widths do not match.")
            if image_dataset.height != label_dataset.height:
                raise RuntimeError("Image and label heights do not match.")
            if image_dataset.transform != label_dataset.transform:
                raise RuntimeError("Image and label transforms do not match.")

            transform = label_dataset.transform
            grid = RasterGridSpec(
                crs=str(label_dataset.crs),
                width=label_dataset.width,
                height=label_dataset.height,
                pixel_size_x=abs(float(transform.a)),
                pixel_size_y=abs(float(transform.e)),
                transform=AffineTransformSpec(
                    a=float(transform.a),
                    b=float(transform.b),
                    c=float(transform.c),
                    d=float(transform.d),
                    e=float(transform.e),
                    f=float(transform.f),
                ),
            )
            labels = label_dataset.read(1)

    grid_id = build_raster_grid_id(grid)

    if grid_id != EXPECTED_GRID_ID:
        raise RuntimeError("Real raster grid identity is not approved.")

    request = TilingRequest(
        image_artifact_path=IMAGE_PATH,
        label_artifact_path=LABEL_PATH,
        grid=grid,
        grid_id=grid_id,
        layout=LOOP1_TILING_LAYOUT,
        output_name="komeh_candidate_tiles_v1",
    )

    catalog = build_tile_catalog(labels, request)
    catalog_id = build_tile_catalog_id(catalog)

    if catalog_id != EXPECTED_CATALOG_ID:
        raise RuntimeError("Real candidate catalog identity is unexpected.")
    if catalog.tile_count != EXPECTED_TILE_COUNT:
        raise RuntimeError("Real candidate tile count is unexpected.")
    catalog_verification_errors = verify_tile_catalog_artifact(
        catalog,
        CATALOG_PATH,
    )

    if catalog_verification_errors:
        raise RuntimeError(
            "Real candidate catalog verification failed: "
            + "; ".join(catalog_verification_errors)
        )
    configs = load_real_reference_source_configs(
        positive_source_id="landslide-reference",
        negative_source_id="negative-reference",
        hard_negative_source_id="hard-negative-reference",
    )
    wired_sources = wire_real_reference_sources(
        configs=configs,
        target_crs=grid.crs,
    )
    ordinary_negative_source = next(
        source
        for source in wired_sources
        if source.vector_source.supervision
        == SupervisionKind.NEGATIVE_REFERENCE
    )

    hard_negative_source = next(
        source
        for source in wired_sources
        if source.vector_source.supervision
        == SupervisionKind.HARD_NEGATIVE_REFERENCE
    )

    if (
        ordinary_negative_source.feature_count
        != EXPECTED_ORDINARY_NEGATIVE_FEATURE_COUNT
    ):
        raise RuntimeError("Ordinary-negative feature count is unexpected.")

    if (
        hard_negative_source.feature_count
        != EXPECTED_HARD_NEGATIVE_FEATURE_COUNT
    ):
        raise RuntimeError("Hard-negative feature count is unexpected.")

    ordinary_negative_mask = rasterize_negative_source_mask(
        ordinary_negative_source.vector_source,
        grid=grid,
    )

    hard_negative_mask = rasterize_negative_source_mask(
        hard_negative_source.vector_source,
        grid=grid,
    )

    ordinary_negative_pixel_count = int(np.count_nonzero(ordinary_negative_mask))
    hard_negative_pixel_count = int(np.count_nonzero(hard_negative_mask))
    shared_negative_pixel_count = int(
        np.count_nonzero(
            ordinary_negative_mask
            & hard_negative_mask
        )
    )

    union_negative_mask = (
        ordinary_negative_mask
        | hard_negative_mask
    )
    union_negative_pixel_count = int(np.count_nonzero(union_negative_mask))

    label_negative_mask = labels == 0
    exact_union_to_label_match = bool(
        np.array_equal(
            union_negative_mask,
            label_negative_mask,
        )
    )

    if (
        ordinary_negative_pixel_count
        != EXPECTED_ORDINARY_NEGATIVE_PIXEL_COUNT
    ):
        raise RuntimeError("Ordinary-negative pixel count is unexpected.")

    if (
        hard_negative_pixel_count
        != EXPECTED_HARD_NEGATIVE_PIXEL_COUNT
    ):
        raise RuntimeError("Hard-negative pixel count is unexpected.")

    if (
        shared_negative_pixel_count
        != EXPECTED_SHARED_NEGATIVE_PIXEL_COUNT
    ):
        raise RuntimeError("Shared negative pixel count is unexpected.")

    if (
        union_negative_pixel_count
        != EXPECTED_UNION_NEGATIVE_PIXEL_COUNT
    ):
        raise RuntimeError("Union negative pixel count is unexpected.")

    if not exact_union_to_label_match:
        raise RuntimeError("Negative source-mask union does not match label value zero.")

    provenance_catalog = build_tile_negative_provenance_catalog(
        catalog=catalog,
        ordinary_negative_mask=ordinary_negative_mask,
        hard_negative_mask=hard_negative_mask,
        ordinary_negative_source_id=ordinary_negative_source.source_id,
        hard_negative_source_id=hard_negative_source.source_id,
    )

    if (
        provenance_catalog.record_count
        != EXPECTED_PROVENANCE_RECORD_COUNT
    ):
        raise RuntimeError("Tile provenance record count is unexpected.")
    selection = select_tile_candidates(
        catalog,
        LOOP1_SAMPLING_POLICY,
    )
    positive_tile_count = sum(
        candidate.label_class == TileLabelClass.POSITIVE
        for candidate in selection.selected_candidates
    )
    negative_only_tile_count = sum(
        candidate.label_class == TileLabelClass.NEGATIVE_ONLY
        for candidate in selection.selected_candidates
    )
    all_ignore_tile_count = sum(
        candidate.label_class == TileLabelClass.ALL_IGNORE
        for candidate in catalog.tiles
    )
    if (
        selection.selected_tile_count
        != EXPECTED_SELECTED_TILE_COUNT
    ):
        raise RuntimeError("Selected supervised tile count is unexpected.")
    if positive_tile_count != EXPECTED_POSITIVE_TILE_COUNT:
        raise RuntimeError("Selected positive tile count is unexpected.")
    if (
        negative_only_tile_count
        != EXPECTED_NEGATIVE_ONLY_TILE_COUNT
    ):
        raise RuntimeError("Selected negative-only tile count is unexpected.")

    if all_ignore_tile_count != EXPECTED_ALL_IGNORE_TILE_COUNT:
        raise RuntimeError("Excluded all-ignore tile count is unexpected.")
    selection_id = build_tile_sampling_selection_id(
        selection,
        catalog=catalog,
    )
    if selection_id != EXPECTED_SELECTION_ID:
        raise RuntimeError("Real sampling selection identity is unexpected.")
    write_tile_sampling_selection_catalog(
        selection,
        catalog=catalog,
        output_path=SELECTION_PATH,
    )
    selection_verification_errors = verify_tile_sampling_selection_artifact(
        selection,
        catalog=catalog,
        artifact_path=SELECTION_PATH,
    )

    if selection_verification_errors:
        raise RuntimeError(
            "Real selection artifact verification failed: "
            + "; ".join(selection_verification_errors)
        )
    all_kind_counts = Counter(
        record.kind
        for record in provenance_catalog.records
    )

    selected_tile_ids = {
        candidate.tile_id
        for candidate in selection.selected_candidates
    }
    selected_records = tuple(
        record
        for record in provenance_catalog.records
        if record.tile_id in selected_tile_ids
    )
    selected_kind_counts = Counter(
        record.kind
        for record in selected_records
    )
    observed_negative_pixel_count = sum(
        record.union_negative_pixel_count
        for record in provenance_catalog.records
    )
    expected_negative_pixel_count = sum(
        candidate.negative_pixel_count
        for candidate in catalog.tiles
    )

    if (observed_negative_pixel_count != expected_negative_pixel_count):
        raise RuntimeError("Tile and catalog negative observations do not match.")

    if (all_kind_counts != Counter(EXPECTED_ALL_PROVENANCE_KIND_COUNTS)):
        raise RuntimeError("All-candidate provenance counts are unexpected.")

    if (selected_kind_counts != Counter(EXPECTED_SELECTED_PROVENANCE_KIND_COUNTS)):
        raise RuntimeError("Selected-tile provenance counts are unexpected.")

    if (
        observed_negative_pixel_count
        != EXPECTED_TILE_NEGATIVE_OBSERVATION_COUNT
    ):
        raise RuntimeError("Tile negative observation count is unexpected.")
    provenance_catalog_id = build_tile_negative_provenance_catalog_id(
        provenance_catalog,
        catalog=catalog,
    )
    if provenance_catalog_id != EXPECTED_PROVENANCE_CATALOG_ID:
        raise RuntimeError("Real provenance catalog identity is unexpected.")

    write_tile_negative_provenance_catalog(
        provenance_catalog,
        catalog=catalog,
        output_path=PROVENANCE_PATH,
    )

    provenance_verification_errors = verify_tile_negative_provenance_artifact(
        provenance_catalog,
        catalog=catalog,
        artifact_path=PROVENANCE_PATH,
    )

    if provenance_verification_errors:
        raise RuntimeError(
            "Real provenance artifact verification failed: "
            + "; ".join(provenance_verification_errors)
        )

    print("Real sampling selection and negative provenance")
    print("=============================")
    print(f"Grid ID: {grid_id}")
    print(f"Catalog ID: {catalog_id}")
    print(f"Provenance catalog ID: {provenance_catalog_id}")
    print(f"Selection ID: {selection_id}")
    print(f"Provenance artifact: {PROVENANCE_PATH}")
    print(f"Selection artifact: {SELECTION_PATH}")
    print(f"Candidate tiles: {catalog.tile_count}")
    print(f"Provenance records: {provenance_catalog.record_count}")

    print()
    print("Source evidence:")
    print(f"  Ordinary-negative features: {ordinary_negative_source.feature_count:,}")
    print(f"  Hard-negative features: {hard_negative_source.feature_count:,}")
    print(f"  Ordinary-negative pixels: {ordinary_negative_pixel_count:,}")
    print(f"  Hard-negative pixels: {hard_negative_pixel_count:,}")
    print(f"  Shared negative pixels: {shared_negative_pixel_count:,}")
    print(f"  Union negative pixels: {union_negative_pixel_count:,}")
    print(f"  Exact union-to-label match: {exact_union_to_label_match}")

    print()
    print("All-candidate provenance:")
    for kind in NegativeProvenanceKind:
        print(f"  {kind.value}: {all_kind_counts[kind]:,}")

    print()
    print("Selected supervised candidates:")
    print(f"  Selected total: {selection.selected_tile_count:,}")
    print(f"  Positive: {positive_tile_count:,}")
    print(f"  Negative only: {negative_only_tile_count:,}")
    print(f"  Excluded all-ignore: {all_ignore_tile_count:,}")
    print()
    print("Selected-tile negative provenance:")

    for kind in NegativeProvenanceKind:
        print(f"  {kind.value}: {selected_kind_counts[kind]:,}")
    print()
    print(f"Tile negative observations: {observed_negative_pixel_count:,}")
    print(f"Catalog negative observations: {expected_negative_pixel_count:,}")
    print(f"Provenance artifact size: {PROVENANCE_PATH.stat().st_size:,} bytes")
    print(f"Selection artifact size: {SELECTION_PATH.stat().st_size:,} bytes")
    print()
    print("PASS: Real sampling selection and tile-level negative provenance were built and reconciled.")


if __name__ == "__main__":
    main()