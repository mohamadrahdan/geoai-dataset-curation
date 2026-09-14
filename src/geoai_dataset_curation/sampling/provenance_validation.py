"Validation of tile-level negative-source provenance"
from geoai_dataset_curation.sampling.contracts import (
    TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileCatalog,
    validate_tile_candidate_record,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


def validate_tile_negative_provenance(
    record: TileNegativeProvenance,
    *,
    candidate: TileCandidateRecord,
) -> tuple[str, ...]:
    "Return consistency errors for one tile provenance record"
    candidate_errors = validate_tile_candidate_record(
        candidate
    )
    if candidate_errors:
        return tuple(
            f"candidate.{error}"
            for error in candidate_errors
        )

    errors: list[str] = []

    if record.tile_id != candidate.tile_id:
        errors.append("tile_id must match the candidate tile_id.")

    count_fields = (
        (
            "ordinary_negative_pixel_count",
            record.ordinary_negative_pixel_count,
        ),
        (
            "hard_negative_pixel_count",
            record.hard_negative_pixel_count,
        ),
        (
            "shared_negative_pixel_count",
            record.shared_negative_pixel_count,
        ),
    )

    for field_name, value in count_fields:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
        ):
            errors.append(
                f"{field_name} must be an integer."
            )
        elif value < 0:
            errors.append(
                f"{field_name} must not be negative."
            )

    counts_are_valid = all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        for _, value in count_fields
    )
    if not counts_are_valid:
        return tuple(errors)
    if (
        record.shared_negative_pixel_count
        > record.ordinary_negative_pixel_count
    ):
        errors.append(
            "shared_negative_pixel_count must not exceed "
            "ordinary_negative_pixel_count."
        )

    if (
        record.shared_negative_pixel_count
        > record.hard_negative_pixel_count
    ):
        errors.append(
            "shared_negative_pixel_count must not exceed "
            "hard_negative_pixel_count."
        )

    if (
        record.union_negative_pixel_count
        != candidate.negative_pixel_count
    ):
        errors.append(
            "source-derived negative union must match the "
            "candidate negative_pixel_count."
        )
    return tuple(errors)


def validate_tile_negative_provenance_catalog(
    provenance: TileNegativeProvenanceCatalog,
    *,
    catalog: TileCatalog,
) -> tuple[str, ...]:
    "Return consistency errors for a provenance catalog"
    catalog_errors = validate_tile_catalog(catalog)
    if catalog_errors:
        return tuple(
            f"catalog.{error}"
            for error in catalog_errors
        )
    errors: list[str] = []

    if (
        provenance.schema_version
        != TILE_NEGATIVE_PROVENANCE_SCHEMA_VERSION
    ):
        errors.append("schema_version is not supported.")

    if (
        provenance.tile_catalog_id
        != build_tile_catalog_id(catalog)
    ):
        errors.append("tile_catalog_id must match the candidate catalog.")
    if not provenance.ordinary_negative_source_id.strip():
        errors.append("ordinary_negative_source_id must not be empty.")
    if not provenance.hard_negative_source_id.strip():
        errors.append("hard_negative_source_id must not be empty.")

    if (
        provenance.ordinary_negative_source_id
        == provenance.hard_negative_source_id
    ):
        errors.append("ordinary and hard-negative source IDs must differ.")

    record_ids = tuple(
        record.tile_id
        for record in provenance.records
    )
    candidate_ids = tuple(
        candidate.tile_id
        for candidate in catalog.tiles
    )

    if len(set(record_ids)) != len(record_ids):
        errors.append("provenance record tile IDs must be unique.")

    if record_ids != candidate_ids:
        errors.append(
            "provenance records must cover the complete catalog "
            "in catalog order."
        )

    candidates_by_id = {
        candidate.tile_id: candidate
        for candidate in catalog.tiles
    }

    for index, record in enumerate(provenance.records):
        candidate = candidates_by_id.get(record.tile_id)
        if candidate is None:
            continue

        record_errors = validate_tile_negative_provenance(
            record,
            candidate=candidate,
        )
        errors.extend(
            f"records[{index}].{error}"
            for error in record_errors
        )

    return tuple(errors)