"Structural and raster-integrity checks for image-mask pairs"
from contextlib import ExitStack
from math import isclose
from pathlib import Path
import rasterio
from rasterio.errors import RasterioIOError
from geoai_dataset_curation.quality_control.contracts import (
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
)
from geoai_dataset_curation.sampling import ImageMaskPairRecord
from geoai_dataset_curation.tiling import TileCandidateRecord


EXPECTED_MASK_DTYPE = "uint8"
EXPECTED_MASK_NODATA = 255


def _error(code: str, message: str) -> QCFinding:
    "Build one blocking raster-integrity finding"
    return QCFinding(
        code=code,
        severity=QCFindingSeverity.ERROR,
        message=message,
    )


def _bounds_match(
    observed_bounds,
    *,
    candidate: TileCandidateRecord,
) -> bool:
    "Return whether raster bounds match the candidate window"
    expected_bounds = (
        candidate.left,
        candidate.bottom,
        candidate.right,
        candidate.top,
    )

    return all(
        isclose(
            observed,
            expected,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        for observed, expected in zip(
            observed_bounds,
            expected_bounds,
            strict=True,
        )
    )


def inspect_pair_raster_integrity(
    pair: ImageMaskPairRecord,
    *,
    candidate: TileCandidateRecord,
    expected_image_band_count: int,
    expected_image_dtype: str,
) -> PairQCResult:
    "Inspect structural integrity of one physical image-mask pair"
    if expected_image_band_count <= 0:
        raise ValueError("expected_image_band_count must be positive.")
    if not expected_image_dtype.strip():
        raise ValueError("expected_image_dtype must not be empty.")
    findings: list[QCFinding] = []
    if pair.tile_id != candidate.tile_id:
        findings.append(
            _error(
                "pair.tile_id_mismatch",
                "Pair tile_id does not match the candidate tile_id.",
            )
        )

    image_path = Path(pair.image_tile_path)
    mask_path = Path(pair.mask_tile_path)
    image_exists = image_path.is_file()
    mask_exists = mask_path.is_file()

    if not image_exists:
        findings.append(
            _error(
                "image.missing",
                "Image artifact does not exist.",
            )
        )

    if not mask_exists:
        findings.append(
            _error(
                "mask.missing",
                "Mask artifact does not exist.",
            )
        )

    with ExitStack() as stack:
        image_dataset = None
        mask_dataset = None

        if image_exists:
            try:
                image_dataset = stack.enter_context(
                    rasterio.open(image_path)
                )
            except RasterioIOError:
                findings.append(
                    _error(
                        "image.unreadable",
                        "Image artifact is not a readable raster.",
                    )
                )

        if mask_exists:
            try:
                mask_dataset = stack.enter_context(
                    rasterio.open(mask_path)
                )
            except RasterioIOError:
                findings.append(
                    _error(
                        "mask.unreadable",
                        "Mask artifact is not a readable raster.",
                    )
                )

        if image_dataset is not None:
            if image_dataset.width != candidate.output_width_pixels:
                findings.append(
                    _error(
                        "image.width_mismatch",
                        "Image width does not match the candidate.",
                    )
                )

            if image_dataset.height != candidate.output_height_pixels:
                findings.append(
                    _error(
                        "image.height_mismatch",
                        "Image height does not match the candidate.",
                    )
                )

            if image_dataset.count != expected_image_band_count:
                findings.append(
                    _error(
                        "image.band_count_mismatch",
                        "Image band count is unexpected.",
                    )
                )

            expected_image_dtypes = (
                expected_image_dtype,
            ) * expected_image_band_count

            if image_dataset.dtypes != expected_image_dtypes:
                findings.append(
                    _error(
                        "image.dtype_mismatch",
                        "Image dtype is unexpected.",
                    )
                )

            if image_dataset.crs is None:
                findings.append(
                    _error(
                        "image.missing_crs",
                        "Image CRS is missing.",
                    )
                )

            if not _bounds_match(
                image_dataset.bounds,
                candidate=candidate,
            ):
                findings.append(
                    _error(
                        "image.bounds_mismatch",
                        "Image bounds do not match the candidate.",
                    )
                )

            try:
                image_dataset.read()
            except (RasterioIOError, OSError):
                findings.append(
                    _error(
                        "image.read_failed",
                        "Image pixel data could not be read.",
                    )
                )

        if mask_dataset is not None:
            if mask_dataset.width != candidate.output_width_pixels:
                findings.append(
                    _error(
                        "mask.width_mismatch",
                        "Mask width does not match the candidate.",
                    )
                )

            if mask_dataset.height != candidate.output_height_pixels:
                findings.append(
                    _error(
                        "mask.height_mismatch",
                        "Mask height does not match the candidate.",
                    )
                )

            if mask_dataset.count != 1:
                findings.append(
                    _error(
                        "mask.band_count_mismatch",
                        "Mask must contain exactly one band.",
                    )
                )

            if mask_dataset.dtypes != (EXPECTED_MASK_DTYPE,):
                findings.append(
                    _error(
                        "mask.dtype_mismatch",
                        "Mask dtype must be uint8.",
                    )
                )

            if mask_dataset.nodata != EXPECTED_MASK_NODATA:
                findings.append(
                    _error(
                        "mask.nodata_mismatch",
                        "Mask nodata value must be 255.",
                    )
                )

            if mask_dataset.crs is None:
                findings.append(
                    _error(
                        "mask.missing_crs",
                        "Mask CRS is missing.",
                    )
                )

            if not _bounds_match(
                mask_dataset.bounds,
                candidate=candidate,
            ):
                findings.append(
                    _error(
                        "mask.bounds_mismatch",
                        "Mask bounds do not match the candidate.",
                    )
                )

            try:
                mask_dataset.read(1)
            except (RasterioIOError, OSError):
                findings.append(
                    _error(
                        "mask.read_failed",
                        "Mask pixel data could not be read.",
                    )
                )

        if (
            image_dataset is not None
            and mask_dataset is not None
        ):
            if image_dataset.crs != mask_dataset.crs:
                findings.append(
                    _error(
                        "pair.crs_mismatch",
                        "Image and mask CRS values differ.",
                    )
                )

            if image_dataset.transform != mask_dataset.transform:
                findings.append(
                    _error(
                        "pair.transform_mismatch",
                        "Image and mask transforms differ.",
                    )
                )

    return PairQCResult(
        pair_id=pair.pair_id,
        tile_id=pair.tile_id,
        findings=tuple(findings),
    )