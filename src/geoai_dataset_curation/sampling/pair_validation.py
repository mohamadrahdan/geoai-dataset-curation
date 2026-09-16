"Validation of image-mask pair contracts and catalogs"
from pathlib import Path
from geoai_dataset_curation.sampling.contracts import (
    IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION,
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
    NegativeProvenanceKind,
    SamplingPolicy,
    TileNegativeProvenance,
    TileNegativeProvenanceCatalog,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.pair_identity import (
    build_image_mask_pair_id,
)
from geoai_dataset_curation.sampling.policy import LOOP1_SAMPLING_POLICY
from geoai_dataset_curation.sampling.provenance_identity import (
    build_tile_negative_provenance_catalog_id,
)
from geoai_dataset_curation.sampling.provenance_validation import (
    validate_tile_negative_provenance,
    validate_tile_negative_provenance_catalog,
)
from geoai_dataset_curation.sampling.selection_identity import (
    build_tile_sampling_selection_id,
)
from geoai_dataset_curation.sampling.selection_validation import (
    validate_tile_sampling_selection,
)
from geoai_dataset_curation.tiling.catalog import (
    TileCandidateRecord,
    TileCatalog,
    TileLabelClass,
    validate_tile_candidate_record,
    validate_tile_catalog,
)
from geoai_dataset_curation.tiling.catalog_identity import (
    build_tile_catalog_id,
)


def _is_sha256_id(value: str) -> bool:
    "Return whether a value is a canonical SHA-256 identity"
    prefix, separator, digest = value.partition(":")
    return (
        prefix == "sha256"
        and separator == ":"
        and len(digest) == 64
        and all(
            character in "0123456789abcdef"
            for character in digest
        )
    )


def _is_tiff_path(value: str) -> bool:
    "Return whether a path uses a supported GeoTIFF suffix"
    return Path(value).suffix.lower() in {".tif", ".tiff"}


def validate_image_mask_pair_record(
    pair: ImageMaskPairRecord,
    *,
    candidate: TileCandidateRecord,
    provenance: TileNegativeProvenance,
) -> tuple[str, ...]:
    "Return consistency errors for one image-mask pair"
    candidate_errors = validate_tile_candidate_record(candidate)
    if candidate_errors:
        return tuple(
            f"candidate.{error}"
            for error in candidate_errors
        )

    provenance_errors = validate_tile_negative_provenance(
        provenance,
        candidate=candidate,
    )
    if provenance_errors:
        return tuple(
            f"provenance.{error}"
            for error in provenance_errors
        )
    errors: list[str] = []

    if not isinstance(pair.pair_id, str) or not _is_sha256_id(pair.pair_id):
        errors.append("pair_id must be a valid SHA-256 identity.")

    if not isinstance(pair.tile_id, str) or not _is_sha256_id(pair.tile_id):
        errors.append("tile_id must be a valid SHA-256 identity.")
    elif pair.tile_id != candidate.tile_id:
        errors.append("tile_id must match the selected candidate.")

    if pair.tile_id != provenance.tile_id:
        errors.append("tile_id must match the provenance record.")

    path_fields = (
        ("image_tile_path", pair.image_tile_path),
        ("mask_tile_path", pair.mask_tile_path),
    )

    for field_name, value in path_fields:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must not be empty.")
        elif not _is_tiff_path(value):
            errors.append(f"{field_name} must use a GeoTIFF suffix.")

    paths_are_valid = all(
        isinstance(value, str) and bool(value.strip())
        for _, value in path_fields
    )
    if paths_are_valid and pair.image_tile_path == pair.mask_tile_path:
        errors.append("image and mask tile paths must differ.")

    label_class_is_valid = isinstance(
        pair.label_class,
        TileLabelClass,
    )
    if not label_class_is_valid:
        errors.append("label_class must be a TileLabelClass.")
    elif pair.label_class != candidate.label_class:
        errors.append("label_class must match the selected candidate.")

    provenance_kind_is_valid = isinstance(
        pair.negative_provenance_kind,
        NegativeProvenanceKind,
    )
    if not provenance_kind_is_valid:
        errors.append(
            "negative_provenance_kind must be "
            "a NegativeProvenanceKind."
        )
    elif pair.negative_provenance_kind != provenance.kind:
        errors.append(
            "negative_provenance_kind must match "
            "the tile provenance."
        )

    if candidate.label_class == TileLabelClass.ALL_IGNORE:
        errors.append("all-ignore candidates must not produce pairs.")

    identity_fields_are_valid = (
        isinstance(pair.pair_id, str)
        and isinstance(pair.tile_id, str)
        and paths_are_valid
        and label_class_is_valid
        and provenance_kind_is_valid
    )
    if (
        identity_fields_are_valid
        and pair.pair_id != build_image_mask_pair_id(pair)):
        errors.append("pair_id must match the pair identity payload.")
    return tuple(errors)


def validate_image_mask_pair_catalog(
    pair_catalog: ImageMaskPairCatalog,
    *,
    tile_catalog: TileCatalog,
    selection: TileSamplingSelection,
    provenance: TileNegativeProvenanceCatalog,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> tuple[str, ...]:
    "Return consistency errors for one image-mask pair catalog"
    tile_catalog_errors = validate_tile_catalog(tile_catalog)
    if tile_catalog_errors:
        return tuple(
            f"tile_catalog.{error}"
            for error in tile_catalog_errors
        )

    selection_errors = validate_tile_sampling_selection(
        selection,
        catalog=tile_catalog,
    )
    if selection_errors:
        return tuple(
            f"selection.{error}"
            for error in selection_errors
        )
    provenance_errors = validate_tile_negative_provenance_catalog(
        provenance,
        catalog=tile_catalog,
    )
    if provenance_errors:
        return tuple(
            f"provenance.{error}"
            for error in provenance_errors
        )
    errors: list[str] = []

    if (
        pair_catalog.schema_version
        != IMAGE_MASK_PAIR_CATALOG_SCHEMA_VERSION):
        errors.append("schema_version is not supported.")
    if not pair_catalog.output_name.strip():
        errors.append("output_name must not be empty.")

    expected_tile_catalog_id = build_tile_catalog_id(tile_catalog)
    expected_selection_id = build_tile_sampling_selection_id(
        selection,
        catalog=tile_catalog,
        policy=policy,
    )
    expected_provenance_catalog_id = (
        build_tile_negative_provenance_catalog_id(
            provenance,
            catalog=tile_catalog,
        )
    )

    if pair_catalog.tile_catalog_id != expected_tile_catalog_id:
        errors.append("tile_catalog_id must match the candidate catalog.")
    if pair_catalog.selection_id != expected_selection_id:
        errors.append("selection_id must match the sampling selection.")

    if (
        pair_catalog.provenance_catalog_id
        != expected_provenance_catalog_id
    ):
        errors.append(
            "provenance_catalog_id must match "
            "the provenance catalog."
        )

    if (
        pair_catalog.source_image_artifact_path
        != tile_catalog.image_artifact_path
    ):
        errors.append(
            "source_image_artifact_path must match "
            "the candidate catalog."
        )

    if (
        pair_catalog.source_label_artifact_path
        != tile_catalog.label_artifact_path
    ):
        errors.append(
            "source_label_artifact_path must match "
            "the candidate catalog."
        )
    selected_ids = tuple(
        candidate.tile_id
        for candidate in selection.selected_candidates
    )
    pair_tile_ids = tuple(
        pair.tile_id
        for pair in pair_catalog.pairs
    )
    if pair_tile_ids != selected_ids:
        errors.append(
            "pairs must cover every selected tile "
            "in selection order."
        )
    pair_ids = tuple(
        pair.pair_id
        for pair in pair_catalog.pairs
    )
    image_paths = tuple(
        pair.image_tile_path
        for pair in pair_catalog.pairs
    )
    mask_paths = tuple(
        pair.mask_tile_path
        for pair in pair_catalog.pairs
    )

    if len(set(pair_ids)) != len(pair_ids):
        errors.append("pair_id values must be unique.")

    if len(set(image_paths)) != len(image_paths):
        errors.append("image tile paths must be unique.")

    if len(set(mask_paths)) != len(mask_paths):
        errors.append("mask tile paths must be unique.")

    if set(image_paths) & set(mask_paths):
        errors.append(
            "image and mask output path sets must not overlap."
        )
    candidates_by_id = {
        candidate.tile_id: candidate
        for candidate in selection.selected_candidates
    }
    provenance_by_id = {
        record.tile_id: record
        for record in provenance.records
    }
    for index, pair in enumerate(pair_catalog.pairs):
        candidate = candidates_by_id.get(pair.tile_id)
        provenance_record = provenance_by_id.get(pair.tile_id)
        if candidate is None or provenance_record is None:
            continue
        pair_errors = validate_image_mask_pair_record(
            pair,
            candidate=candidate,
            provenance=provenance_record,
        )
        errors.extend(
            f"pairs[{index}].{error}"
            for error in pair_errors
        )
    return tuple(errors)