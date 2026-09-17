"Serialization and persistence for deterministic tile selections"
import json
from pathlib import Path
from typing import Any
from geoai_dataset_curation.sampling.contracts import (
    SamplingPolicy,
    TileSamplingSelection,
)
from geoai_dataset_curation.sampling.policy import LOOP1_SAMPLING_POLICY
from geoai_dataset_curation.sampling.selection_identity import (
    build_tile_sampling_selection_id,
    tile_sampling_selection_identity_payload,
)
from geoai_dataset_curation.tiling.catalog import TileCatalog
from geoai_dataset_curation.tiling.catalog_io import (
    tile_candidate_record_to_dict,
)


def tile_sampling_selection_to_dict(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> dict[str, Any]:
    "Serialize one validated deterministic tile selection"
    identity_payload = tile_sampling_selection_identity_payload(
        selection,
        catalog=catalog,
        policy=policy,
    )
    return {
        "selection_id": build_tile_sampling_selection_id(
            selection,
            catalog=catalog,
            policy=policy,
        ),
        "schema_version": identity_payload["schema_version"],
        "tile_catalog_id": identity_payload["tile_catalog_id"],
        "policy": identity_payload["policy"],
        "selected_tile_count": selection.selected_tile_count,
        "selected_positive_tile_count": (
            selection.selected_positive_tile_count
        ),
        "selected_negative_only_tile_count": (
            selection.selected_negative_only_tile_count
        ),
        "excluded_tile_count": selection.excluded_tile_count,
        "selected_tiles": [
            tile_candidate_record_to_dict(candidate)
            for candidate in selection.selected_candidates
        ],
        "excluded_tile_ids": identity_payload["excluded_tile_ids"],
    }


def write_tile_sampling_selection_catalog(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
    output_path: Path,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> Path:
    "Write one deterministic selection as canonical JSON"
    payload = tile_sampling_selection_to_dict(
        selection,
        catalog=catalog,
        policy=policy,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output_path


def verify_tile_sampling_selection_artifact(
    selection: TileSamplingSelection,
    *,
    catalog: TileCatalog,
    artifact_path: Path,
    policy: SamplingPolicy = LOOP1_SAMPLING_POLICY,
) -> tuple[str, ...]:
    "Verify a persisted selection artifact against its expected value"
    if not artifact_path.is_file():
        return ("selection artifact does not exist.",)
    try:
        observed = json.loads(
            artifact_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("selection artifact must contain valid UTF-8 JSON.",)
    expected = tile_sampling_selection_to_dict(
        selection,
        catalog=catalog,
        policy=policy,
    )
    if observed != expected:
        return (
            "selection artifact content does not match "
            "expected selection.",
        )
    return ()