"Cross-artifact traceability checks for image-mask pairs"
from pathlib import Path
from geoai_dataset_curation.quality_control.contracts import (
    QCFinding,
    QCFindingSeverity,
    TraceabilityQCResult,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
    build_image_mask_pair_catalog_id,
    validate_image_mask_pair_catalog,
    verify_image_mask_pair_artifacts,
)
from geoai_dataset_curation.tiling import TileCatalog


TIFF_SUFFIXES = {".tif", ".tiff"}


def _error(code: str, message: str) -> QCFinding:
    "Build one blocking traceability finding"

    return QCFinding(
        code=code,
        severity=QCFindingSeverity.ERROR,
        message=message,
    )


def _discover_tiff_files(
    expected_paths: tuple[Path, ...],
) -> set[Path]:
    "Discover GeoTIFF files in expected output directories"
    directories = {
        path.parent
        for path in expected_paths
    }
    discovered: set[Path] = set()

    for directory in directories:
        if not directory.is_dir():
            continue

        discovered.update(
            path
            for path in directory.iterdir()
            if (
                path.is_file()
                and path.suffix.lower() in TIFF_SUFFIXES
            )
        )

    return discovered


def inspect_cross_artifact_traceability(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
) -> TraceabilityQCResult:
    "Verify catalog links and the physical pair population"

    findings: list[QCFinding] = []

    image_paths = tuple(
        Path(pair.image_tile_path)
        for pair in pair_catalog.pairs
    )
    mask_paths = tuple(
        Path(pair.mask_tile_path)
        for pair in pair_catalog.pairs
    )

    expected_image_paths = set(image_paths)
    expected_mask_paths = set(mask_paths)
    discovered_image_paths = _discover_tiff_files(
        image_paths
    )
    discovered_mask_paths = _discover_tiff_files(
        mask_paths
    )

    for path in sorted(
        expected_image_paths - discovered_image_paths,
        key=lambda value: value.as_posix(),
    ):
        findings.append(
            _error(
                "traceability.image_missing",
                f"Expected image artifact is missing: {path.as_posix()}",
            )
        )

    for path in sorted(
        expected_mask_paths - discovered_mask_paths,
        key=lambda value: value.as_posix(),
    ):
        findings.append(
            _error(
                "traceability.mask_missing",
                f"Expected mask artifact is missing: {path.as_posix()}",
            )
        )

    for path in sorted(
        discovered_image_paths - expected_image_paths,
        key=lambda value: value.as_posix(),
    ):
        findings.append(
            _error(
                "traceability.unexpected_image",
                f"Unexpected image artifact exists: {path.as_posix()}",
            )
        )

    for path in sorted(
        discovered_mask_paths - expected_mask_paths,
        key=lambda value: value.as_posix(),
    ):
        findings.append(
            _error(
                "traceability.unexpected_mask",
                f"Unexpected mask artifact exists: {path.as_posix()}",
            )
        )

    catalog_errors = validate_image_mask_pair_catalog(
        pair_catalog,
        tile_catalog=tile_catalog,
        selection=selection,
        provenance=provenance,
    )

    for error in catalog_errors:
        findings.append(
            _error(
                "traceability.catalog_validation_failed",
                error,
            )
        )

    verified_pair_count = 0

    if not catalog_errors:
        artifact_verification = (
            verify_image_mask_pair_artifacts(
                pair_catalog,
                tile_catalog=tile_catalog,
                selection=selection,
                provenance=provenance,
            )
        )
        verified_pair_count = (
            artifact_verification.verified_pair_count
        )

        for error in artifact_verification.errors:
            findings.append(
                _error(
                    "traceability.artifact_verification_failed",
                    error,
                )
            )

    return TraceabilityQCResult(
        pair_catalog_id=(
            build_image_mask_pair_catalog_id(
                pair_catalog
            )
        ),
        expected_pair_count=pair_catalog.pair_count,
        verified_pair_count=verified_pair_count,
        discovered_image_file_count=len(
            discovered_image_paths
        ),
        discovered_mask_file_count=len(
            discovered_mask_paths
        ),
        findings=tuple(findings),
    )