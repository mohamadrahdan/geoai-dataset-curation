"Build and verify the real Loop 1 candidate tile catalog"
from pathlib import Path
import rasterio
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.image_construction.grid_identity import (
    build_raster_grid_id,
)
from geoai_dataset_curation.tiling import (
    LOOP1_TILING_LAYOUT,
    TileLabelClass,
    TilingRequest,
    build_tile_catalog,
    build_tile_catalog_id,
    build_tile_layout_id,
    verify_tile_catalog_artifact,
    write_tile_catalog,
)


IMAGE_PATH = Path("artifacts/live/loop1/komeh_sentinel2_2024_median.tif")
LABEL_PATH = Path("artifacts/live/loop1/komeh_labels_v1.tif")
CATALOG_PATH = Path("artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json")
EXPECTED_GRID_ID = (
    "sha256:"
    "d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799"
)
EXPECTED_TILE_COUNT = 870
EXPECTED_POSITIVE_TILE_COUNT = 19
EXPECTED_NEGATIVE_ONLY_TILE_COUNT = 31
EXPECTED_ALL_IGNORE_TILE_COUNT = 820


def main() -> None:
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"Image artifact not found: {IMAGE_PATH}")
    if not LABEL_PATH.is_file():
        raise FileNotFoundError(f"Label artifact not found: {LABEL_PATH}")
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
    positive_tile_count = sum(
        record.label_class == TileLabelClass.POSITIVE
        for record in catalog.tiles
    )
    negative_only_tile_count = sum(
        record.label_class == TileLabelClass.NEGATIVE_ONLY
        for record in catalog.tiles
    )
    all_ignore_tile_count = sum(
        record.label_class == TileLabelClass.ALL_IGNORE
        for record in catalog.tiles
    )
    supervised_tile_count = sum(
        record.supervised_pixel_count > 0
        for record in catalog.tiles
    )
    if catalog.tile_count != EXPECTED_TILE_COUNT:
        raise RuntimeError("Real catalog tile count is unexpected.")
    if positive_tile_count != EXPECTED_POSITIVE_TILE_COUNT:
        raise RuntimeError("Real positive tile count is unexpected.")
    if negative_only_tile_count != EXPECTED_NEGATIVE_ONLY_TILE_COUNT:
        raise RuntimeError("Real negative-only tile count is unexpected.")
    if all_ignore_tile_count != EXPECTED_ALL_IGNORE_TILE_COUNT:
        raise RuntimeError("Real all-ignore tile count is unexpected.")
    if any(record.padding_pixel_count != 0 for record in catalog.tiles):
        raise RuntimeError("Selected Loop 1 catalog must not contain padding.")

    write_tile_catalog(catalog, CATALOG_PATH)
    verification_errors = verify_tile_catalog_artifact(
        catalog,
        CATALOG_PATH,
    )
    if verification_errors:
        raise RuntimeError(
            "Real catalog verification failed: "
            + "; ".join(verification_errors)
        )

    print("Loop 1 real candidate tile catalog")
    print("==================================")
    print(f"Image path: {IMAGE_PATH}")
    print(f"Label path: {LABEL_PATH}")
    print(f"Catalog path: {CATALOG_PATH}")
    print(f"Catalog ID: {build_tile_catalog_id(catalog)}")
    print(f"Grid ID: {catalog.grid_id}")
    print(f"Layout ID: {build_tile_layout_id(LOOP1_TILING_LAYOUT)}")
    print(f"Tile count: {catalog.tile_count}")
    print(f"Supervised tiles: {supervised_tile_count}")
    print(f"Positive tiles: {positive_tile_count}")
    print(f"Negative-only tiles: {negative_only_tile_count}")
    print(f"All-ignore tiles: {all_ignore_tile_count}")
    print(f"Catalog size: {CATALOG_PATH.stat().st_size:,} bytes")
    print()
    print("PASS: Real candidate tile catalog was written and verified.")


if __name__ == "__main__":
    main()