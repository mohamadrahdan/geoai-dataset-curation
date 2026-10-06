"Semantic quality checks for image-mask pair masks"
from pathlib import Path
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from geoai_dataset_curation.quality_control.contracts import (
    PairQCResult,
    QCFinding,
    QCFindingSeverity,
)
from geoai_dataset_curation.sampling import ImageMaskPairRecord
from geoai_dataset_curation.tiling import (
    TileCandidateRecord,
    TileLabelClass,
)


ALLOWED_MASK_VALUES = {0, 1, 255}


def _error(code: str, message: str) -> QCFinding:
    "Build one blocking mask-semantic finding"
    return QCFinding(
        code=code,
        severity=QCFindingSeverity.ERROR,
        message=message,
    )


def inspect_pair_mask_semantics(
    pair: ImageMaskPairRecord,
    *,
    candidate: TileCandidateRecord,
) -> PairQCResult:
    "Inspect semantic consistency of one physical mask"
    findings: list[QCFinding] = []

    if pair.label_class != candidate.label_class:
        findings.append(_error("pair.label_class_mismatch", "Pair label_class does not match the candidate."))

    if pair.label_class == TileLabelClass.ALL_IGNORE:
        findings.append(_error("pair.all_ignore_label_forbidden", "An all-ignore pair is forbidden."))

    mask_path = Path(pair.mask_tile_path)

    if not mask_path.is_file():
        findings.append(_error("mask.missing", "Mask artifact does not exist."))
        return PairQCResult(
            pair_id=pair.pair_id,
            tile_id=pair.tile_id,
            findings=tuple(findings),
        )

    try:
        with rasterio.open(mask_path) as mask_dataset:
            observed_mask = mask_dataset.read(1)
    except (RasterioIOError, OSError):
        findings.append(_error("mask.unreadable", "Mask artifact is not a readable raster."))
        return PairQCResult(
            pair_id=pair.pair_id,
            tile_id=pair.tile_id,
            findings=tuple(findings),
        )

    observed_values = {
        int(value)
        for value in np.unique(observed_mask)
    }
    unsupported_values = tuple(
        sorted(observed_values - ALLOWED_MASK_VALUES)
    )

    if unsupported_values:
        findings.append(
            _error(
                "mask.unsupported_values",
                f"Mask contains unsupported values: {unsupported_values}.",
            )
        )

    positive_count = int(
        np.count_nonzero(observed_mask == 1)
    )
    negative_count = int(
        np.count_nonzero(observed_mask == 0)
    )
    ignore_count = int(
        np.count_nonzero(observed_mask == 255)
    )
    observed_pixel_count = int(observed_mask.size)
    classified_pixel_count = (
        positive_count
        + negative_count
        + ignore_count
    )
    expected_pixel_count = (
        candidate.output_width_pixels
        * candidate.output_height_pixels
    )

    if observed_pixel_count != expected_pixel_count:
        findings.append(_error("mask.pixel_count_mismatch", "Mask pixel count does not match the candidate output size."))

    if classified_pixel_count != observed_pixel_count:
        findings.append(_error("mask.pixel_partition_mismatch", "Positive, negative, and ignore counts do not cover every mask pixel."))

    if positive_count != candidate.positive_pixel_count:
        findings.append(_error("mask.positive_count_mismatch", "Positive pixel count does not match the candidate."))

    if negative_count != candidate.negative_pixel_count:
        findings.append(_error("mask.negative_count_mismatch", "Negative pixel count does not match the candidate."))

    if ignore_count != candidate.ignore_pixel_count:
        findings.append(_error("mask.ignore_count_mismatch", "Ignore pixel count does not match the candidate."))

    if ignore_count == observed_pixel_count:
        findings.append(_error("mask.all_ignore", "A selected mask must not be entirely ignore."))

    if (
        candidate.label_class == TileLabelClass.POSITIVE
        and positive_count == 0
    ):
        findings.append(_error("mask.positive_label_mismatch", "A positive candidate must contain positive pixels."))

    if candidate.label_class == TileLabelClass.NEGATIVE_ONLY:
        if positive_count != 0:
            findings.append(_error("mask.negative_only_label_mismatch", "A negative-only candidate must not contain positive pixels."))

        if negative_count == 0:
            findings.append(_error("mask.missing_negative_pixels", "A negative-only candidate must contain negative pixels."))

    if candidate.label_class == TileLabelClass.ALL_IGNORE:
        findings.append(_error("candidate.all_ignore_forbidden", "An all-ignore candidate must not enter pair quality control."))

    return PairQCResult(
        pair_id=pair.pair_id,
        tile_id=pair.tile_id,
        findings=tuple(findings),
    )