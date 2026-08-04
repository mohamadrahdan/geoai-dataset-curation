"Environment loading for Earth Engine configuration"

import os
from collections.abc import Mapping
from geoai_dataset_curation.image_construction.earth_engine_config import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
)


PROJECT_ID_ENV = "GEOAI_EE_PROJECT_ID"
CREDENTIAL_SOURCE_ENV = "GEOAI_EE_CREDENTIAL_SOURCE"
SERVICE_ACCOUNT_EMAIL_ENV = "GEOAI_EE_SERVICE_ACCOUNT_EMAIL"
SERVICE_ACCOUNT_KEY_PATH_ENV = "GEOAI_EE_SERVICE_ACCOUNT_KEY_PATH"
API_ENDPOINT_ENV = "GEOAI_EE_API_ENDPOINT"


def _optional_environment_value(
    environment: Mapping[str, str],
    name: str,
) -> str | None:
    "Return one stripped optional environment value"
    value = environment.get(name)

    if value is None:
        return None

    stripped = value.strip()

    return stripped or None


def load_earth_engine_config(
    environment: Mapping[str, str] | None = None,
) -> EarthEngineConfig:
    "Load Earth Engine configuration from environment variables"
    source = os.environ if environment is None else environment

    project_id = source.get(PROJECT_ID_ENV, "").strip()
    credential_source_value = source.get(
        CREDENTIAL_SOURCE_ENV,
        EarthEngineCredentialSource.PERSISTENT.value,
    ).strip()

    try:
        credential_source = EarthEngineCredentialSource(
            credential_source_value
        )
    except ValueError as error:
        allowed_values = ", ".join(
            item.value for item in EarthEngineCredentialSource
        )
        raise ValueError(
            f"{CREDENTIAL_SOURCE_ENV} must be one of: "
            f"{allowed_values}."
        ) from error

    return EarthEngineConfig(
        project_id=project_id,
        credential_source=credential_source,
        service_account_email=_optional_environment_value(
            source,
            SERVICE_ACCOUNT_EMAIL_ENV,
        ),
        service_account_key_path=_optional_environment_value(
            source,
            SERVICE_ACCOUNT_KEY_PATH_ENV,
        ),
        api_endpoint=_optional_environment_value(
            source,
            API_ENDPOINT_ENV,
        ),
    )