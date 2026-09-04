"Runtime wiring of real private reference vectors into label contracts"
from dataclasses import dataclass
from pathlib import Path
import geopandas as gpd
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.label_rasterization.contracts import (
    LabelVectorSource,
)
from geoai_dataset_curation.validation import (
    validate_vector_file,
)
from geoai_dataset_curation.label_rasterization.geometry_repair import (
    GeometryRepairSummary,
    repair_invalid_reference_geometries,
)
from geoai_dataset_curation.validation import (
    validate_source,
    validate_source_metadata,
)


@dataclass(frozen=True)
class RealReferenceSourceConfig:
    "Runtime configuration for one private reference-vector source"
    source_id: str
    path: Path
    supervision: SupervisionKind


@dataclass(frozen=True)
class WiredReferenceSource:
    "One validated and grid-ready real reference source"
    source_id: str
    source_path: Path
    source_crs: str
    target_crs: str
    feature_count: int
    repair_summary: GeometryRepairSummary
    vector_source: LabelVectorSource


def wire_real_reference_source(
    *,
    config: RealReferenceSourceConfig,
    target_crs: str,
) -> WiredReferenceSource:
    "Load, repair, validate, reproject, and convert one real reference source"

    if not config.path.is_file():
        raise FileNotFoundError(
            f"Reference source does not exist: {config.path}"
        )

    frame = gpd.read_file(config.path)

    if frame.crs is None:
        raise ValueError(
            f"Reference source has no CRS: {config.source_id}"
        )

    source_crs = frame.crs.to_string()

    repaired, repair_summary = (
        repair_invalid_reference_geometries(frame)
    )

    metadata_issues = validate_source_metadata(repaired)
    geometry_summary = validate_source(
        source_id=config.source_id,
        geometries=repaired.geometry,
    )

    issues = (
        metadata_issues
        + geometry_summary.issues
    )

    if issues:
        issue_codes = ", ".join(
            issue.code
            for issue in issues
        )
        raise ValueError(
            f"Reference source failed validation after repair: "
            f"{config.source_id}: {issue_codes}"
        )

    projected = repaired.to_crs(target_crs)

    geometries = tuple(projected.geometry)

    return WiredReferenceSource(
        source_id=config.source_id,
        source_path=config.path,
        source_crs=source_crs,
        target_crs=target_crs,
        feature_count=len(projected),
        repair_summary=repair_summary,
        vector_source=LabelVectorSource(
            source_id=config.source_id,
            supervision=config.supervision,
            geometries=geometries,
        ),
    )


def wire_real_reference_sources(
    *,
    configs: tuple[RealReferenceSourceConfig, ...],
    target_crs: str,
) -> tuple[WiredReferenceSource, ...]:
    "Wire multiple real reference sources to one target CRS"
    return tuple(
        wire_real_reference_source(
            config=config,
            target_crs=target_crs,
        )
        for config in configs
    )