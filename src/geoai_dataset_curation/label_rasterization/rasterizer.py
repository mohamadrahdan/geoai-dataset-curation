"Rasterization of validated label-vector sources onto an exact grid"
from dataclasses import dataclass
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from geoai_dataset_curation.contracts import (
    LabelValue,
    SupervisionKind,
    get_label_schema_entry,
)
from geoai_dataset_curation.label_rasterization.contracts import (
    LabelRasterizationRequest,
    LabelVectorSource,
)
from geoai_dataset_curation.label_rasterization.validation import (
    validate_label_rasterization_request,
)
from typing import cast


@dataclass(frozen=True)
class LabelRasterizationResult:
    "In-memory result of one label-rasterization execution"
    data: np.ndarray
    burned_feature_count: int


def _target_value(
    source: LabelVectorSource,
) -> int:
    "Resolve one supervision kind to its numeric training target"
    entry = get_label_schema_entry(source.supervision)
    return int(entry.target)


def _rasterize_source_mask(
    *,
    source: LabelVectorSource,
    request: LabelRasterizationRequest,
) -> np.ndarray:
    "Rasterize one vector source into a boolean coverage mask"
    transform = request.grid.transform

    if transform is None:
        raise ValueError(
            "Exact rasterization requires an affine transform."
        )

    mask = cast(
        np.ndarray,
        rasterize(
            (
                (geometry, 1)
                for geometry in source.geometries
            ),
            out_shape=(
                request.grid.height,
                request.grid.width,
            ),
            transform=Affine(*transform.as_tuple),
            fill=0,
            all_touched=False,
            dtype="uint8",
        ),
    )

    return mask.astype(bool)


def rasterize_label_request(
    request: LabelRasterizationRequest,
) -> LabelRasterizationResult:
    "Rasterize validated label sources using the Loop 1 label policy"
    errors = validate_label_rasterization_request(
        request
    )
    if errors:
        raise ValueError(
            "Invalid label rasterization request: "
            + "; ".join(errors)
        )
    output = np.full(
        (
            request.grid.height,
            request.grid.width,
        ),
        int(LabelValue.IGNORE),
        dtype=np.uint8,
    )
    assigned = np.zeros(
        output.shape,
        dtype=bool,
    )
    burned_feature_count = 0
    for source in request.sources:
        source_mask = _rasterize_source_mask(
            source=source,
            request=request,
        )
        target = _target_value(source)
        conflict_mask = (
            source_mask
            & assigned
            & (output != target)
        )
        if np.any(conflict_mask):
            raise ValueError(
                "Conflicting supervision detected during "
                f"rasterization: {source.source_id}"
            )
        output[source_mask] = target
        assigned[source_mask] = True
        burned_feature_count += len(
            source.geometries
        )
    return LabelRasterizationResult(
        data=output,
        burned_feature_count=burned_feature_count,
    )