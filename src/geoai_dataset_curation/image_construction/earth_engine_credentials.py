"Credential strategies for Earth Engine initialization"

from dataclasses import dataclass
from geoai_dataset_curation.image_construction.earth_engine_config import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
)
from geoai_dataset_curation.image_construction.earth_engine_config_validation import (
    validate_earth_engine_config,
)


@dataclass(frozen=True)
class EarthEngineCredentialStrategy:
    "Authentication behavior derived from one valid configuration"
    credential_source: EarthEngineCredentialSource
    uses_explicit_credentials: bool
    allows_interactive_authentication: bool
    service_account_email: str | None = None
    service_account_key_path: str | None = None


def build_earth_engine_credential_strategy(
    config: EarthEngineConfig,
) -> EarthEngineCredentialStrategy:
    "Build the credential strategy for one valid configuration"
    errors = validate_earth_engine_config(config)

    if errors:
        raise ValueError(
            "Cannot build Earth Engine credential strategy: "
            + "; ".join(errors)
        )

    if (
        config.credential_source
        is EarthEngineCredentialSource.PERSISTENT
    ):
        return EarthEngineCredentialStrategy(
            credential_source=config.credential_source,
            uses_explicit_credentials=False,
            allows_interactive_authentication=True,
        )

    if (
        config.credential_source
        is EarthEngineCredentialSource.APPLICATION_DEFAULT
    ):
        return EarthEngineCredentialStrategy(
            credential_source=config.credential_source,
            uses_explicit_credentials=False,
            allows_interactive_authentication=False,
        )

    return EarthEngineCredentialStrategy(
        credential_source=config.credential_source,
        uses_explicit_credentials=True,
        allows_interactive_authentication=False,
        service_account_email=config.service_account_email,
        service_account_key_path=config.service_account_key_path,
    )