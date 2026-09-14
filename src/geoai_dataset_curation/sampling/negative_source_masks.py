"Rasterization of explicit negative sources into boolean masks"
import numpy as np
from geoai_dataset_curation.contracts import (
    LabelValue,
    SupervisionKind,
)
from geoai_dataset_curation.image_construction.contracts import (
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization.contracts import (
    LabelRasterizationRequest,
    LabelVectorSource,
)
from geoai_dataset_curation.label_rasterization.rasterizer import (
    rasterize_label_request,
)


NEGATIVE_SOURCE_KINDS = {
    SupervisionKind.NEGATIVE_REFERENCE,
    SupervisionKind.HARD_NEGATIVE_REFERENCE,
}


def rasterize_negative_source_mask(
    source: LabelVectorSource,
    *,
    grid: RasterGridSpec,
) -> np.ndarray:
    "Rasterize one explicit negative source as a boolean mask"
    if source.supervision not in NEGATIVE_SOURCE_KINDS:
        raise ValueError(
            "source must use NEGATIVE_REFERENCE or "
            "HARD_NEGATIVE_REFERENCE supervision."
        )

    result = rasterize_label_request(
        LabelRasterizationRequest(
            sources=(source,),
            grid=grid,
            output_name=(
                f"{source.source_id}_negative_source_mask"
            ),
        )
    )

    return result.data == int(LabelValue.NEGATIVE)