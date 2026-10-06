from pathlib import Path
import pytest
from geoai_dataset_curation.quality_control import (
    QCStatus,
    inspect_cross_artifact_traceability,
)
from geoai_dataset_curation.quality_control import (
    traceability,
)
from geoai_dataset_curation.sampling import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairArtifactVerification,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
)
from geoai_dataset_curation.tiling import TileLabelClass


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)
TILE_CATALOG_ID = "sha256:" + ("c" * 64)
SELECTION_ID = "sha256:" + ("d" * 64)
PROVENANCE_ID = "sha256:" + ("e" * 64)


def make_pair_catalog(
    tmp_path: Path,
) -> tuple[
    ImageMaskPairCatalog,
    Path,
    Path,
]:
    image_path = tmp_path / "images" / "pair.tif"
    mask_path = tmp_path / "masks" / "pair.tif"

    pair = ImageMaskPairRecord(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path=image_path.as_posix(),
        mask_tile_path=mask_path.as_posix(),
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=(
            NegativeProvenanceKind.NONE
        ),
    )

    catalog = ImageMaskPairCatalog(
        schema_version=(
            IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION
        ),
        output_name="test-pairs",
        tile_catalog_id=TILE_CATALOG_ID,
        selection_id=SELECTION_ID,
        provenance_catalog_id=PROVENANCE_ID,
        source_image_artifact_path="source-image.tif",
        source_label_artifact_path="source-label.tif",
        pairs=(pair,),
    )

    return catalog, image_path, mask_path


def patch_valid_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        traceability,
        "validate_image_mask_pair_catalog",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        traceability,
        "verify_image_mask_pair_artifacts",
        lambda *_args, **_kwargs: (
            ImageMaskPairArtifactVerification(
                expected_pair_count=1,
                verified_pair_count=1,
                errors=(),
            )
        ),
    )


def inspect(
    catalog: ImageMaskPairCatalog,
):
    return inspect_cross_artifact_traceability(
        catalog,
        tile_catalog=object(),  # type: ignore[arg-type]
        selection=object(),  # type: ignore[arg-type]
        provenance=object(),  # type: ignore[arg-type]
    )


def test_valid_cross_artifact_traceability_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog, image_path, mask_path = (
        make_pair_catalog(tmp_path)
    )
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"image")
    mask_path.write_bytes(b"mask")
    patch_valid_verification(monkeypatch)

    result = inspect(catalog)
    assert result.status == QCStatus.PASS
    assert result.expected_pair_count == 1
    assert result.verified_pair_count == 1
    assert result.discovered_image_file_count == 1
    assert result.discovered_mask_file_count == 1
    assert result.findings == ()


def test_catalog_validation_errors_become_qc_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog, image_path, mask_path = (
        make_pair_catalog(tmp_path)
    )
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"image")
    mask_path.write_bytes(b"mask")

    monkeypatch.setattr(
        traceability,
        "validate_image_mask_pair_catalog",
        lambda *_args, **_kwargs: (
            "selection_id must match the sampling selection.",
        ),
    )

    result = inspect(catalog)
    assert result.status == QCStatus.FAIL
    assert result.verified_pair_count == 0
    assert tuple(
        finding.code
        for finding in result.findings
    ) == (
        "traceability.catalog_validation_failed",
    )


def test_missing_and_unexpected_files_fail_traceability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog, image_path, mask_path = (
        make_pair_catalog(tmp_path)
    )
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    mask_path.write_bytes(b"mask")
    unexpected_image = (
        image_path.parent / "unexpected.tif"
    )
    unexpected_image.write_bytes(b"unexpected")
    patch_valid_verification(monkeypatch)

    result = inspect(catalog)
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert result.discovered_image_file_count == 1
    assert "traceability.image_missing" in finding_codes
    assert "traceability.unexpected_image" in finding_codes


def test_artifact_verification_errors_become_qc_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog, image_path, mask_path = (
        make_pair_catalog(tmp_path)
    )
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"image")
    mask_path.write_bytes(b"mask")

    monkeypatch.setattr(
        traceability,
        "validate_image_mask_pair_catalog",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        traceability,
        "verify_image_mask_pair_artifacts",
        lambda *_args, **_kwargs: (
            ImageMaskPairArtifactVerification(
                expected_pair_count=1,
                verified_pair_count=0,
                errors=(
                    "pairs[0].image pixels differ from source.",
                ),
            )
        ),
    )
    result = inspect(catalog)
    assert result.status == QCStatus.FAIL
    assert result.verified_pair_count == 0
    assert tuple(
        finding.code
        for finding in result.findings
    ) == (
        "traceability.artifact_verification_failed",
    )