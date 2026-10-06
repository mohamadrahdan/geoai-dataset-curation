"Content-quality inspection for physical image tiles"
from pathlib import Path
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from geoai_dataset_curation.quality_control.contracts import (
    ImageBandStatistics,
    ImageContentInspection,
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
)
from geoai_dataset_curation.sampling import ImageMaskPairRecord


def _error(code: str, message: str) -> QCFinding:
    "Build one blocking image-content finding"

    return QCFinding(
        code=code,
        severity=QCFindingSeverity.ERROR,
        message=message,
    )


def _warning(code: str, message: str) -> QCFinding:
    "Build one non-blocking image-content finding"

    return QCFinding(
        code=code,
        severity=QCFindingSeverity.WARNING,
        message=message,
    )


def inspect_pair_image_content(
    pair: ImageMaskPairRecord,
) -> ImageContentInspection:
    "Inspect image values and calculate per-band statistics"
    findings: list[QCFinding] = []
    statistics: list[ImageBandStatistics] = []
    image_path = Path(pair.image_tile_path)

    if not image_path.is_file():
        findings.append(_error("image.missing", "Image artifact does not exist."))
        return ImageContentInspection(
            pair_result=PairQCResult(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                findings=tuple(findings),
            ),
            band_statistics=(),
        )

    try:
        with rasterio.open(image_path) as image_dataset:
            image = image_dataset.read()
    except (RasterioIOError, OSError):
        findings.append(_error("image.unreadable", "Image artifact is not a readable raster."))
        return ImageContentInspection(
            pair_result=PairQCResult(
                pair_id=pair.pair_id,
                tile_id=pair.tile_id,
                findings=tuple(findings),
            ),
            band_statistics=(),
        )

    for band_offset, band in enumerate(image):
        band_index = band_offset + 1
        numeric_band = band.astype(
            np.float64,
            copy=False,
        )
        finite_mask = np.isfinite(numeric_band)
        pixel_count = int(numeric_band.size)
        finite_pixel_count = int(
            np.count_nonzero(finite_mask)
        )
        non_finite_pixel_count = (
            pixel_count - finite_pixel_count
        )

        if non_finite_pixel_count:
            findings.append(
                _error(
                    "image.non_finite_values",
                    f"Band {band_index} contains {non_finite_pixel_count} non-finite pixels.",
                )
            )

        if finite_pixel_count == 0:
            statistics.append(
                ImageBandStatistics(
                    band_index=band_index,
                    pixel_count=pixel_count,
                    finite_pixel_count=0,
                    non_finite_pixel_count=(
                        non_finite_pixel_count
                    ),
                    minimum=None,
                    maximum=None,
                    mean=None,
                    standard_deviation=None,
                )
            )
            findings.append(
                _error(
                    "image.no_finite_values",
                    f"Band {band_index} contains no finite pixels.",
                )
            )
            continue

        finite_values = numeric_band[finite_mask]
        minimum = float(np.min(finite_values))
        maximum = float(np.max(finite_values))
        mean = float(np.mean(finite_values))
        standard_deviation = float(
            np.std(finite_values)
        )

        band_statistics = ImageBandStatistics(
            band_index=band_index,
            pixel_count=pixel_count,
            finite_pixel_count=finite_pixel_count,
            non_finite_pixel_count=(
                non_finite_pixel_count
            ),
            minimum=minimum,
            maximum=maximum,
            mean=mean,
            standard_deviation=standard_deviation,
        )
        statistics.append(band_statistics)

        if band_statistics.is_constant:
            findings.append(
                _warning(
                    "image.constant_band",
                    f"Band {band_index} is constant.",
                )
            )

    image_is_finite = bool(
        np.all(np.isfinite(image))
    )

    if image.size > 0 and image_is_finite:
        if bool(np.all(image == 0)):
            findings.append(_error("image.all_zero", "Image contains only zero values."))
        elif bool(np.all(image == image.flat[0])):
            findings.append(_warning("image.constant", "All image values are identical."))

    return ImageContentInspection(
        pair_result=PairQCResult(
            pair_id=pair.pair_id,
            tile_id=pair.tile_id,
            findings=tuple(findings),
        ),
        band_statistics=tuple(statistics),
    )