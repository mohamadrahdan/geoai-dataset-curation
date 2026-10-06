from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.quality_control import (
    QCStatus,
    inspect_pair_image_content,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairRecord,
    NegativeProvenanceKind,
)
from geoai_dataset_curation.tiling import TileLabelClass


PAIR_ID = "sha256:" + ("a" * 64)
TILE_ID = "sha256:" + ("b" * 64)
TRANSFORM = from_origin(0.0, 40.0, 10.0, 10.0)
CRS = "EPSG:32639"


def make_pair(image_path: Path) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path=image_path.as_posix(),
        mask_tile_path="unused-mask.tif",
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=(
            NegativeProvenanceKind.ORDINARY_NEGATIVE
        ),
    )


def write_image(
    path: Path,
    data: np.ndarray,
) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=data.shape[2],
        height=data.shape[1],
        count=data.shape[0],
        dtype=str(data.dtype),
        crs=CRS,
        transform=TRANSFORM,
    ) as dataset:
        dataset.write(data)


def varying_image() -> np.ndarray:
    return np.arange(
        64,
        dtype=np.float64,
    ).reshape(4, 4, 4)


def test_valid_image_produces_band_statistics(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    write_image(image_path, varying_image())

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )

    assert inspection.status == QCStatus.PASS
    assert inspection.pair_result.findings == ()
    assert len(inspection.band_statistics) == 4

    first_band = inspection.band_statistics[0]
    assert first_band.band_index == 1
    assert first_band.pixel_count == 16
    assert first_band.finite_pixel_count == 16
    assert first_band.non_finite_pixel_count == 0
    assert first_band.minimum == 0.0
    assert first_band.maximum == 15.0
    assert first_band.mean == pytest.approx(7.5)
    assert first_band.standard_deviation == pytest.approx(
        4.6097722286464435
    )
    assert first_band.is_constant is False


def test_non_finite_values_fail_image_content_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    image = varying_image()
    image[0, 0, 0] = np.nan
    image[1, 0, 0] = np.inf
    write_image(image_path, image)

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )
    finding_codes = tuple(
        finding.code
        for finding in inspection.pair_result.findings
    )

    assert inspection.status == QCStatus.FAIL
    assert finding_codes.count(
        "image.non_finite_values"
    ) == 2
    assert (
        inspection.band_statistics[0]
        .non_finite_pixel_count
        == 1
    )
    assert (
        inspection.band_statistics[1]
        .non_finite_pixel_count
        == 1
    )


def test_constant_band_produces_warning(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    image = varying_image()
    image[0] = 5.0
    write_image(image_path, image)

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )
    assert inspection.status == QCStatus.WARNING
    assert tuple(
        finding.code
        for finding in inspection.pair_result.findings
    ) == ("image.constant_band",)
    assert inspection.band_statistics[0].is_constant is True


def test_all_zero_image_fails_content_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    image = np.zeros(
        (4, 4, 4),
        dtype=np.float64,
    )
    write_image(image_path, image)

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )
    finding_codes = {
        finding.code
        for finding in inspection.pair_result.findings
    }
    assert inspection.status == QCStatus.FAIL
    assert "image.all_zero" in finding_codes
    assert "image.constant_band" in finding_codes


def test_fully_constant_nonzero_image_warns(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    image = np.full(
        (4, 4, 4),
        12.0,
        dtype=np.float64,
    )
    write_image(image_path, image)

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )
    finding_codes = {
        finding.code
        for finding in inspection.pair_result.findings
    }
    assert inspection.status == QCStatus.WARNING
    assert "image.constant" in finding_codes
    assert "image.constant_band" in finding_codes


def test_unreadable_image_fails_content_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    image_path.write_text(
        "not a raster",
        encoding="utf-8",
    )

    inspection = inspect_pair_image_content(
        make_pair(image_path)
    )
    assert inspection.status == QCStatus.FAIL
    assert inspection.band_statistics == ()
    assert tuple(
        finding.code
        for finding in inspection.pair_result.findings
    ) == ("image.unreadable",)