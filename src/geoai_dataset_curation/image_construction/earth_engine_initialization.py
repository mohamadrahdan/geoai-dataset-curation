"Coordination of Earth Engine initialization"
from dataclasses import dataclass
from geoai_dataset_curation.image_construction.earth_engine_config import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
)
from geoai_dataset_curation.image_construction.earth_engine_credentials import (
    build_earth_engine_credential_strategy,
)
from geoai_dataset_curation.image_construction.earth_engine_runtime import (
    EarthEngineRuntime,
)


@dataclass(frozen=True)
class EarthEngineInitializationResult:
    "Traceable result of one successful Earth Engine initialization"
    project_id: str
    credential_source: EarthEngineCredentialSource
    api_endpoint: str | None


def initialize_earth_engine(
    *,
    config: EarthEngineConfig,
    runtime: EarthEngineRuntime,
) -> EarthEngineInitializationResult:
    "Initialize Earth Engine through the SDK-neutral runtime boundary"
    strategy = build_earth_engine_credential_strategy(config)

    if (
        strategy.credential_source
        is EarthEngineCredentialSource.PERSISTENT
    ):
        runtime.initialize_with_persistent_credentials(
            project_id=config.project_id,
            api_endpoint=config.api_endpoint,
        )

    elif (
        strategy.credential_source
        is EarthEngineCredentialSource.APPLICATION_DEFAULT
    ):
        runtime.initialize_with_application_default_credentials(
            project_id=config.project_id,
            api_endpoint=config.api_endpoint,
        )

    else:
        if (
            strategy.service_account_email is None
            or strategy.service_account_key_path is None
        ):
            raise RuntimeError(
                "Validated service-account strategy is incomplete."
            )

        runtime.initialize_with_service_account_credentials(
            project_id=config.project_id,
            service_account_email=strategy.service_account_email,
            service_account_key_path=(
                strategy.service_account_key_path
            ),
            api_endpoint=config.api_endpoint,
        )

    return EarthEngineInitializationResult(
        project_id=config.project_id,
        credential_source=strategy.credential_source,
        api_endpoint=config.api_endpoint,
    )