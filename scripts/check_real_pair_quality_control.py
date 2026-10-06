"Run pair quality control against the real Loop 1 artifacts."
from pathlib import Path
from geoai_dataset_curation.quality_control.artifact_loading import (
    load_pair_qc_input_artifacts,
)
from geoai_dataset_curation.quality_control.report import (
    run_pair_quality_control,
    write_pair_qc_report,
)
from geoai_dataset_curation.quality_control.visual_review import (
    generate_pair_contact_sheets,
)
from geoai_dataset_curation.quality_control.visual_review_io import (
    build_visual_review_template,
    read_visual_review_catalog,
    write_visual_review_catalog,
)


ARTIFACT_ROOT = Path("artifacts/live/loop1")

TILE_CATALOG_PATH = ARTIFACT_ROOT / "komeh_candidate_tiles_v1.catalog.json"
SELECTION_PATH = ARTIFACT_ROOT / "komeh_sampling_selection_v1.catalog.json"
PROVENANCE_PATH = ARTIFACT_ROOT / "komeh_tile_negative_provenance_v1.catalog.json"
PAIR_CATALOG_PATH = ARTIFACT_ROOT / "komeh_image_mask_pairs_v1.catalog.json"

QC_REPORT_PATH = ARTIFACT_ROOT / "komeh_image_mask_pairs_v1.qc.json"
CONTACT_SHEET_DIRECTORY = ARTIFACT_ROOT / "komeh_image_mask_pairs_v1_visual_review"
VISUAL_REVIEW_PATH = ARTIFACT_ROOT / "komeh_image_mask_pairs_v1.visual_review.json"

EXPECTED_IMAGE_BAND_COUNT = 4
EXPECTED_IMAGE_DTYPE = "float64"
REVIEWER = "Mohammad Rahdan"
PAIRS_PER_PAGE = 5


def main() -> None:
    inputs = load_pair_qc_input_artifacts(
        tile_catalog_path=TILE_CATALOG_PATH,
        selection_path=SELECTION_PATH,
        provenance_path=PROVENANCE_PATH,
        pair_catalog_path=PAIR_CATALOG_PATH,
    )

    report = run_pair_quality_control(
        inputs.pair_catalog,
        tile_catalog=inputs.tile_catalog,
        selection=inputs.selection,
        provenance=inputs.provenance,
        expected_image_band_count=EXPECTED_IMAGE_BAND_COUNT,
        expected_image_dtype=EXPECTED_IMAGE_DTYPE,
    )
    write_pair_qc_report(report, QC_REPORT_PATH)

    expected_contact_sheet_count = (
        inputs.pair_catalog.pair_count + PAIRS_PER_PAGE - 1
    ) // PAIRS_PER_PAGE
    existing_contact_sheet_paths = tuple(
        sorted(CONTACT_SHEET_DIRECTORY.glob("contact_sheet_*.png"))
    )

    if existing_contact_sheet_paths:
        if len(existing_contact_sheet_paths) != expected_contact_sheet_count:
            raise RuntimeError("Existing contact-sheet count is incomplete.")
        contact_sheet_paths = existing_contact_sheet_paths
    else:
        contact_sheet_paths = generate_pair_contact_sheets(
            inputs.pair_catalog,
            output_directory=CONTACT_SHEET_DIRECTORY,
            rgb_band_indices=(3, 2, 1),
            tile_size=256,
            pairs_per_page=PAIRS_PER_PAGE,
        )

    if VISUAL_REVIEW_PATH.is_file():
        read_visual_review_catalog(
            VISUAL_REVIEW_PATH,
            pair_catalog=inputs.pair_catalog,
            require_complete=False,
        )
        review_template_created = False
    else:
        review_template = build_visual_review_template(
            inputs.pair_catalog,
            output_name="komeh_image_mask_pairs_v1_visual_review",
            reviewer=REVIEWER,
        )
        write_visual_review_catalog(
            review_template,
            pair_catalog=inputs.pair_catalog,
            output_path=VISUAL_REVIEW_PATH,
            require_complete=False,
        )
        review_template_created = True

    print(f"Pair catalog: {PAIR_CATALOG_PATH}")
    print(f"Pair count: {inputs.pair_catalog.pair_count}")
    print(f"Automated QC report: {QC_REPORT_PATH}")
    print(f"Contact sheets: {len(contact_sheet_paths)}")
    print(f"Contact-sheet directory: {CONTACT_SHEET_DIRECTORY}")
    print(f"Visual-review catalog: {VISUAL_REVIEW_PATH}")
    print(f"Visual-review template created: {review_template_created}")


if __name__ == "__main__":
    main()