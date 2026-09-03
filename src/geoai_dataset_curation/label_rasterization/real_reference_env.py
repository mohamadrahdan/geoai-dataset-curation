"Environment loading for private reference-vector paths"
import os
from pathlib import Path
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.label_rasterization.real_reference_wiring import (
    RealReferenceSourceConfig,
)


POSITIVE_REFERENCE_PATH_ENV = "GEOAI_POSITIVE_REFERENCE_PATH"
NEGATIVE_REFERENCE_PATH_ENV = "GEOAI_NEGATIVE_REFERENCE_PATH"
HARD_NEGATIVE_REFERENCE_PATH_ENV = "GEOAI_HARD_NEGATIVE_REFERENCE_PATH"


def load_real_reference_source_configs(
    *,
    positive_source_id: str,
    negative_source_id: str,
    hard_negative_source_id: str,
) -> tuple[RealReferenceSourceConfig, ...]:
    "Load real private reference-source configuration from environment"
    required = {
        POSITIVE_REFERENCE_PATH_ENV: (
            positive_source_id,
            SupervisionKind.POSITIVE_REFERENCE,
        ),
        NEGATIVE_REFERENCE_PATH_ENV: (
            negative_source_id,
            SupervisionKind.NEGATIVE_REFERENCE,
        ),
        HARD_NEGATIVE_REFERENCE_PATH_ENV: (
            hard_negative_source_id,
            SupervisionKind.HARD_NEGATIVE_REFERENCE,
        ),
    }
    configs: list[RealReferenceSourceConfig] = []

    for env_name, (
        source_id,
        supervision,
    ) in required.items():
        value = os.getenv(env_name)
        if value is None or not value.strip():
            raise ValueError(
                f"Required environment variable is missing: {env_name}"
            )
        configs.append(
            RealReferenceSourceConfig(
                source_id=source_id,
                path=Path(value),
                supervision=supervision,
            )
        )
    return tuple(configs)