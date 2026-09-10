"Contracts and validation for deterministic candidate tile catalogs"
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


TILE_CATALOG_SCHEMA_VERSION = "tile-catalog-v1"


class TileLabelClass(StrEnum):
    "Label-derived class of one candidate tile"
    POSITIVE = "positive"
    NEGATIVE_ONLY = "negative_only"
    ALL_IGNORE = "all_ignore"


@dataclass(frozen=True)
class TileCandidateRecord:
    "Persistent record for one deterministic candidate tile"
    tile_id: str
    grid_id: str
    layout_id: str
    row_index: int
    column_index: int
    row_offset_pixels: int
    column_offset_pixels: int
    read_width_pixels: int
    read_height_pixels: int
    output_width_pixels: int
    output_height_pixels: int
    left: float
    bottom: float
    right: float
    top: float
    positive_pixel_count: int
    negative_pixel_count: int
    ignore_pixel_count: int

    @property
    def output_pixel_count(self) -> int:
        "Return the complete output-tile pixel count"
        return self.output_width_pixels * self.output_height_pixels

    @property
    def read_pixel_count(self) -> int:
        "Return the number of pixels read from the source raster"
        return self.read_width_pixels * self.read_height_pixels

    @property
    def padding_pixel_count(self) -> int:
        "Return the number of artificial output pixels"
        return self.output_pixel_count - self.read_pixel_count

    @property
    def supervised_pixel_count(self) -> int:
        "Return the number of explicitly supervised pixels"
        return self.positive_pixel_count + self.negative_pixel_count

    @property
    def positive_fraction(self) -> float:
        "Return positive pixels as a fraction of the output tile"
        if self.output_pixel_count == 0:
            return 0.0
        return self.positive_pixel_count / self.output_pixel_count

    @property
    def label_class(self) -> TileLabelClass:
        "Return the label-derived candidate class"
        if self.positive_pixel_count > 0:
            return TileLabelClass.POSITIVE
        if self.negative_pixel_count > 0:
            return TileLabelClass.NEGATIVE_ONLY
        return TileLabelClass.ALL_IGNORE


@dataclass(frozen=True)
class TileCatalog:
    "Persistent deterministic candidate tile population"
    schema_version: str
    output_name: str
    image_artifact_path: str
    label_artifact_path: str
    grid_id: str
    layout_id: str
    tiles: tuple[TileCandidateRecord, ...]

    @property
    def tile_count(self) -> int:
        "Return the number of candidate records"
        return len(self.tiles)


def _is_sha256_id(value: str) -> bool:
    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def validate_tile_candidate_record(
    record: TileCandidateRecord,
    *,
    expected_grid_id: str | None = None,
    expected_layout_id: str | None = None,
) -> tuple[str, ...]:
    "Return consistency errors for one candidate tile record"
    errors: list[str] = []
    for field_name, value in (
        ("tile_id", record.tile_id),
        ("grid_id", record.grid_id),
        ("layout_id", record.layout_id),
    ):
        if not _is_sha256_id(value):
            errors.append(f"{field_name} must be a valid SHA-256 identity.")

    for field_name, value in (
        ("row_index", record.row_index),
        ("column_index", record.column_index),
        ("row_offset_pixels", record.row_offset_pixels),
        ("column_offset_pixels", record.column_offset_pixels),
    ):
        if value < 0:
            errors.append(f"{field_name} must not be negative.")

    for field_name, value in (
        ("read_width_pixels", record.read_width_pixels),
        ("read_height_pixels", record.read_height_pixels),
        ("output_width_pixels", record.output_width_pixels),
        ("output_height_pixels", record.output_height_pixels),
    ):
        if value <= 0:
            errors.append(f"{field_name} must be positive.")
    if record.read_width_pixels > record.output_width_pixels:
        errors.append("read_width_pixels must not exceed output_width_pixels.")
    if record.read_height_pixels > record.output_height_pixels:
        errors.append("read_height_pixels must not exceed output_height_pixels.")

    for field_name, value in (
        ("positive_pixel_count", record.positive_pixel_count),
        ("negative_pixel_count", record.negative_pixel_count),
        ("ignore_pixel_count", record.ignore_pixel_count),
    ):
        if value < 0:
            errors.append(f"{field_name} must not be negative.")
    observed_pixel_count = (
        record.positive_pixel_count
        + record.negative_pixel_count
        + record.ignore_pixel_count
    )
    if observed_pixel_count != record.output_pixel_count:
        errors.append("label pixel counts must equal the output pixel count.")
    if not all(
        isfinite(value)
        for value in (record.left, record.bottom, record.right, record.top)
    ):
        errors.append("tile bounds must contain only finite values.")
    if record.left >= record.right:
        errors.append("left must be smaller than right.")
    if record.bottom >= record.top:
        errors.append("bottom must be smaller than top.")
    if expected_grid_id is not None and record.grid_id != expected_grid_id:
        errors.append("grid_id must match the catalog grid_id.")
    if expected_layout_id is not None and record.layout_id != expected_layout_id:
        errors.append("layout_id must match the catalog layout_id.")

    return tuple(errors)


def validate_tile_catalog(catalog: TileCatalog) -> tuple[str, ...]:
    "Return consistency errors for one candidate tile catalog"
    errors: list[str] = []
    if catalog.schema_version != TILE_CATALOG_SCHEMA_VERSION:
        errors.append("schema_version is not supported.")
    for field_name, value in (
        ("output_name", catalog.output_name),
        ("image_artifact_path", catalog.image_artifact_path),
        ("label_artifact_path", catalog.label_artifact_path),
    ):
        if not value.strip():
            errors.append(f"{field_name} must not be empty.")
    if not _is_sha256_id(catalog.grid_id):
        errors.append("grid_id must be a valid SHA-256 identity.")
    if not _is_sha256_id(catalog.layout_id):
        errors.append("layout_id must be a valid SHA-256 identity.")
    if not catalog.tiles:
        errors.append("tiles must not be empty.")
        return tuple(errors)

    for index, record in enumerate(catalog.tiles):
        record_errors = validate_tile_candidate_record(
            record,
            expected_grid_id=catalog.grid_id,
            expected_layout_id=catalog.layout_id,
        )
        errors.extend(f"tiles[{index}]: {error}" for error in record_errors)

    tile_ids = tuple(record.tile_id for record in catalog.tiles)
    if len(set(tile_ids)) != len(tile_ids):
        errors.append("tile_id values must be unique.")
    positions = tuple(
        (record.row_index, record.column_index)
        for record in catalog.tiles
    )
    if len(set(positions)) != len(positions):
        errors.append("tile row and column positions must be unique.")
    if positions != tuple(sorted(positions)):
        errors.append("tiles must use deterministic row-major ordering.")

    return tuple(errors)