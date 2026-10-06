from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.quality_control import (
    QCStatus,
    QCFinding,
    QCFindingSeverity,
    TraceabilityQCResult,
    pair_qc_report_to_dict,
    run_pair_quality_control,
    write_pair_qc_report,
)
from geoai_dataset_curation.quality_control import report
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    TileSamplingSelection,
)
from geoai_dataset_curation.tiling import TileCandidateRecord, TileLabelClass


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)
GRID_ID = "sha256:" + ("c" * 64)
LAYOUT_ID = "sha256:" + ("d" * 64)
TRANSFORM = from_origin(0.0, 40.0, 10.0, 10.0)
CRS = "EPSG:32639"


def make_candidate() -> TileCandidateRecord:
    return TileCandidateRecord(
        tile_id=TILE_ID,
        grid_id=GRID_ID,
        layout_id=LAYOUT_ID,
        row_index=0,
        column_index=0,
        row_offset_pixels=0,
        column_offset_pixels=0,
        read_width_pixels=4,
        read_height_pixels=4,
        output_width_pixels=4,
        output_height_pixels=4,
        left=0.0,
        bottom=0.0,
        right=40.0,
        top=40.0,
        positive_pixel_count=1,
        negative_pixel_count=1,
        ignore_pixel_count=14,
    )


def write_pair_files(root: Path, *, constant_first_band: bool = False) -> tuple[Path, Path]:
    image_path = root / "images" / "pair.tif"
    mask_path = root / "masks" / "pair.tif"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)

    image = np.arange(64, dtype=np.float64).reshape(4, 4, 4)
    if constant_first_band:
        image[0] = 5.0

    mask = np.full((4, 4), 255, dtype=np.uint8)
    mask[0, 0] = 1
    mask[0, 1] = 0

    with rasterio.open(
        image_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=4,
        dtype="float64",
        crs=CRS,
        transform=TRANSFORM,
    ) as dataset:
        dataset.write(image)

    with rasterio.open(
        mask_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=TRANSFORM,
        nodata=255,
    ) as dataset:
        dataset.write(mask, 1)

    return image_path, mask_path


def make_context(image_path: Path, mask_path: Path):
    candidate = make_candidate()
    pair = ImageMaskPairRecord(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path=image_path.as_posix(),
        mask_tile_path=mask_path.as_posix(),
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=NegativeProvenanceKind.ORDINARY_NEGATIVE,
    )
    pair_catalog = ImageMaskPairCatalog(
        schema_version=IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
        output_name="qc-pairs",
        tile_catalog_id="sha256:" + ("e" * 64),
        selection_id="sha256:" + ("f" * 64),
        provenance_catalog_id="sha256:" + ("1" * 64),
        source_image_artifact_path="source-image.tif",
        source_label_artifact_path="source-label.tif",
        pairs=(pair,),
    )
    selection = TileSamplingSelection(
        catalog_id=pair_catalog.tile_catalog_id,
        selected_candidates=(candidate,),
        excluded_tile_ids=(),
    )
    return pair_catalog, selection


def patch_traceability_pass(monkeypatch) -> None:
    monkeypatch.setattr(
        report,
        "inspect_cross_artifact_traceability",
        lambda *_args, **_kwargs: TraceabilityQCResult(
            pair_catalog_id="sha256:" + ("2" * 64),
            expected_pair_count=1,
            verified_pair_count=1,
            discovered_image_file_count=1,
            discovered_mask_file_count=1,
            findings=(),
        ),
    )


def run_report(pair_catalog, selection):
    return run_pair_quality_control(
        pair_catalog,
        tile_catalog=object(),  # type: ignore[arg-type]
        selection=selection,
        provenance=object(),  # type: ignore[arg-type]
        expected_image_band_count=4,
        expected_image_dtype="float64",
    )


def test_valid_pair_population_passes_automated_qc(tmp_path: Path, monkeypatch) -> None:
    image_path, mask_path = write_pair_files(tmp_path)
    pair_catalog, selection = make_context(image_path, mask_path)
    patch_traceability_pass(monkeypatch)

    qc_report = run_report(pair_catalog, selection)
    assert qc_report.status == QCStatus.PASS
    assert qc_report.pair_count == 1
    assert qc_report.pass_count == 1
    assert qc_report.finding_count == 0
    assert len(qc_report.image_statistics[0].bands) == 4


def test_duplicate_findings_are_removed(tmp_path: Path, monkeypatch) -> None:
    image_path = tmp_path / "images" / "missing.tif"
    mask_path = tmp_path / "masks" / "pair.tif"
    mask_path.parent.mkdir(parents=True)
    mask = np.full((4, 4), 255, dtype=np.uint8)
    mask[0, 0] = 1
    mask[0, 1] = 0

    with rasterio.open(
        mask_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=TRANSFORM,
        nodata=255,
    ) as dataset:
        dataset.write(mask, 1)

    pair_catalog, selection = make_context(image_path, mask_path)
    patch_traceability_pass(monkeypatch)

    qc_report = run_report(pair_catalog, selection)
    image_missing_count = sum(
        finding.code == "image.missing"
        for finding in qc_report.pair_results[0].findings
    )
    assert qc_report.status == QCStatus.FAIL
    assert image_missing_count == 1


def test_constant_band_produces_report_warning(tmp_path: Path, monkeypatch) -> None:
    image_path, mask_path = write_pair_files(tmp_path, constant_first_band=True)
    pair_catalog, selection = make_context(image_path, mask_path)
    patch_traceability_pass(monkeypatch)

    qc_report = run_report(pair_catalog, selection)
    assert qc_report.status == QCStatus.WARNING
    assert qc_report.warning_count == 1


def test_traceability_failure_controls_report_status(tmp_path: Path, monkeypatch) -> None:
    image_path, mask_path = write_pair_files(tmp_path)
    pair_catalog, selection = make_context(image_path, mask_path)

    monkeypatch.setattr(
        report,
        "inspect_cross_artifact_traceability",
        lambda *_args, **_kwargs: TraceabilityQCResult(
            pair_catalog_id="sha256:" + ("2" * 64),
            expected_pair_count=1,
            verified_pair_count=0,
            discovered_image_file_count=1,
            discovered_mask_file_count=1,
            findings=(
                QCFinding(
                    code="traceability.failed",
                    severity=QCFindingSeverity.ERROR,
                    message="Traceability failed.",
                ),
            ),
        ),
    )

    qc_report = run_report(pair_catalog, selection)
    assert qc_report.status == QCStatus.FAIL
    assert qc_report.fail_count == 0
    assert qc_report.finding_count == 1


def test_qc_report_serialization_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    image_path, mask_path = write_pair_files(tmp_path)
    pair_catalog, selection = make_context(image_path, mask_path)
    patch_traceability_pass(monkeypatch)
    qc_report = run_report(pair_catalog, selection)

    first_path = write_pair_qc_report(qc_report, tmp_path / "first.json")
    second_path = write_pair_qc_report(qc_report, tmp_path / "second.json")
    payload = pair_qc_report_to_dict(qc_report)
    assert payload["status"] == "pass"
    assert payload["summary"]["pair_count"] == 1
    assert first_path.read_bytes() == second_path.read_bytes()