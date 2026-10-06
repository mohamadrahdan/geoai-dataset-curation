from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.quality_control import (
    QCStatus,
    inspect_pair_raster_integrity,
)
from geoai_dataset_curation.sampling import (
    ImageMaskPairRecord,
    NegativeProvenanceKind,
)
from geoai_dataset_curation.tiling import (
    TileCandidateRecord,
    TileLabelClass,
)


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


def make_pair(
    image_path: Path,
    mask_path: Path,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path=image_path.as_posix(),
        mask_tile_path=mask_path.as_posix(),
        label_class=TileLabelClass.POSITIVE,
        negative_provenance_kind=(
            NegativeProvenanceKind.ORDINARY_NEGATIVE
        ),
    )


def write_image(
    path: Path,
    *,
    count: int = 4,
    dtype: str = "float64",
    transform=TRANSFORM,
) -> None:
    data = np.ones(
        (count, 4, 4),
        dtype=dtype,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=count,
        dtype=dtype,
        crs=CRS,
        transform=transform,
    ) as dataset:
        dataset.write(data)


def write_mask(
    path: Path,
    *,
    dtype: str = "uint8",
    transform=TRANSFORM,
    nodata: int | None = 255,
) -> None:
    data = np.full(
        (4, 4),
        255,
        dtype=dtype,
    )
    data[0, 0] = 1
    data[0, 1] = 0

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype=dtype,
        crs=CRS,
        transform=transform,
        nodata=nodata,
    ) as dataset:
        dataset.write(data, 1)


def inspect(
    image_path: Path,
    mask_path: Path,
):
    return inspect_pair_raster_integrity(
        make_pair(image_path, mask_path),
        candidate=make_candidate(),
        expected_image_band_count=4,
        expected_image_dtype="float64",
    )


def test_valid_pair_passes_raster_integrity(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    mask_path = tmp_path / "mask.tif"
    write_image(image_path)
    write_mask(mask_path)

    result = inspect(image_path, mask_path)
    assert result.status == QCStatus.PASS
    assert result.findings == ()


def test_missing_pair_artifacts_fail_qc(
    tmp_path: Path,
) -> None:
    result = inspect(
        tmp_path / "missing-image.tif",
        tmp_path / "missing-mask.tif",
    )
    assert result.status == QCStatus.FAIL
    assert {
        finding.code
        for finding in result.findings
    } == {
        "image.missing",
        "mask.missing",
    }


def test_unreadable_pair_artifacts_fail_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    mask_path = tmp_path / "mask.tif"
    image_path.write_text("not a raster", encoding="utf-8")
    mask_path.write_text("not a raster", encoding="utf-8")
    result = inspect(image_path, mask_path)
    assert result.status == QCStatus.FAIL
    assert {
        finding.code
        for finding in result.findings
    } == {
        "image.unreadable",
        "mask.unreadable",
    }


def test_unexpected_image_structure_fails_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    mask_path = tmp_path / "mask.tif"
    write_image(
        image_path,
        count=3,
        dtype="float32",
    )
    write_mask(mask_path)
    result = inspect(image_path, mask_path)
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "image.band_count_mismatch" in finding_codes
    assert "image.dtype_mismatch" in finding_codes


def test_misaligned_mask_fails_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    mask_path = tmp_path / "mask.tif"
    shifted_transform = from_origin(
        10.0,
        40.0,
        10.0,
        10.0,
    )

    write_image(image_path)
    write_mask(
        mask_path,
        transform=shifted_transform,
    )
    result = inspect(image_path, mask_path)
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.bounds_mismatch" in finding_codes
    assert "pair.transform_mismatch" in finding_codes


def test_invalid_mask_metadata_fails_qc(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.tif"
    mask_path = tmp_path / "mask.tif"
    write_image(image_path)
    write_mask(
        mask_path,
        dtype="uint16",
        nodata=None,
    )

    result = inspect(image_path, mask_path)
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.dtype_mismatch" in finding_codes
    assert "mask.nodata_mismatch" in finding_codes