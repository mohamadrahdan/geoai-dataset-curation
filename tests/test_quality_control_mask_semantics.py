from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from geoai_dataset_curation.quality_control import (
    QCStatus,
    inspect_pair_mask_semantics,
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


def make_candidate(
    *,
    label_class: TileLabelClass = TileLabelClass.POSITIVE,
) -> TileCandidateRecord:
    counts = {
        TileLabelClass.POSITIVE: (1, 1, 14),
        TileLabelClass.NEGATIVE_ONLY: (0, 1, 15),
        TileLabelClass.ALL_IGNORE: (0, 0, 16),
    }
    positive, negative, ignore = counts[label_class]

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
        positive_pixel_count=positive,
        negative_pixel_count=negative,
        ignore_pixel_count=ignore,
    )


def make_pair(
    mask_path: Path,
    *,
    label_class: TileLabelClass = TileLabelClass.POSITIVE,
) -> ImageMaskPairRecord:
    return ImageMaskPairRecord(
        pair_id=PAIR_ID,
        tile_id=TILE_ID,
        image_tile_path="unused-image.tif",
        mask_tile_path=mask_path.as_posix(),
        label_class=label_class,
        negative_provenance_kind=(
            NegativeProvenanceKind.ORDINARY_NEGATIVE
        ),
    )


def write_mask(
    path: Path,
    data: np.ndarray,
) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=data.shape[1],
        height=data.shape[0],
        count=1,
        dtype=str(data.dtype),
        crs=CRS,
        transform=TRANSFORM,
        nodata=255,
    ) as dataset:
        dataset.write(data, 1)


def positive_mask() -> np.ndarray:
    mask = np.full(
        (4, 4),
        255,
        dtype=np.uint8,
    )
    mask[0, 0] = 1
    mask[0, 1] = 0
    return mask


def test_valid_positive_mask_passes_semantic_qc(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    write_mask(mask_path, positive_mask())

    result = inspect_pair_mask_semantics(
        make_pair(mask_path),
        candidate=make_candidate(),
    )
    assert result.status == QCStatus.PASS
    assert result.findings == ()


def test_unsupported_mask_value_fails_semantic_qc(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    mask = positive_mask()
    mask[1, 1] = 7
    write_mask(mask_path, mask)

    result = inspect_pair_mask_semantics(
        make_pair(mask_path),
        candidate=make_candidate(),
    )
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.unsupported_values" in finding_codes
    assert "mask.pixel_partition_mismatch" in finding_codes


def test_candidate_pixel_counts_must_match_mask(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    mask = positive_mask()
    mask[1, 1] = 1
    write_mask(mask_path, mask)

    result = inspect_pair_mask_semantics(
        make_pair(mask_path),
        candidate=make_candidate(),
    )
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.positive_count_mismatch" in finding_codes
    assert "mask.ignore_count_mismatch" in finding_codes


def test_negative_only_mask_must_not_contain_positive_pixels(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    write_mask(mask_path, positive_mask())
    result = inspect_pair_mask_semantics(
        make_pair(
            mask_path,
            label_class=TileLabelClass.NEGATIVE_ONLY,
        ),
        candidate=make_candidate(
            label_class=TileLabelClass.NEGATIVE_ONLY,
        ),
    )
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.negative_only_label_mismatch" in finding_codes


def test_all_ignore_mask_fails_semantic_qc(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    mask = np.full(
        (4, 4),
        255,
        dtype=np.uint8,
    )
    write_mask(mask_path, mask)

    result = inspect_pair_mask_semantics(
        make_pair(mask_path),
        candidate=make_candidate(),
    )
    finding_codes = {
        finding.code
        for finding in result.findings
    }
    assert result.status == QCStatus.FAIL
    assert "mask.all_ignore" in finding_codes
    assert "mask.positive_label_mismatch" in finding_codes


def test_unreadable_mask_fails_semantic_qc(
    tmp_path: Path,
) -> None:
    mask_path = tmp_path / "mask.tif"
    mask_path.write_text(
        "not a raster",
        encoding="utf-8",
    )

    result = inspect_pair_mask_semantics(
        make_pair(mask_path),
        candidate=make_candidate(),
    )
    assert result.status == QCStatus.FAIL
    assert tuple(
        finding.code
        for finding in result.findings
    ) == ("mask.unreadable",)