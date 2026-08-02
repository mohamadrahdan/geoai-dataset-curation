"Validation rules for Earth Engine configuration"
from pathlib import Path
from urllib.parse import urlparse
from geoai_dataset_curation.image_construction.earth_engine_config import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
)


def _is_https_url(value: str) -> bool:
    "Return whether one value is an absolute HTTPS URL"
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
    )


def validate_earth_engine_config(
    config: EarthEngineConfig,
) -> tuple[str, ...]:
    "Return validation errors for one Earth Engine configuration"
    errors: list[str] = []
    
    if not config.project_id.strip():
        errors.append("project_id must not be empty.")

    if config.api_endpoint is not None:
        endpoint = config.api_endpoint.strip()

        if not endpoint:
            errors.append(
                "api_endpoint must not be empty when provided."
            )
        elif not _is_https_url(endpoint):
            errors.append(
                "api_endpoint must be an absolute HTTPS URL."
            )

    if (
        config.credential_source
        is EarthEngineCredentialSource.SERVICE_ACCOUNT
    ):
        if (
            config.service_account_email is None
            or not config.service_account_email.strip()
        ):
            errors.append(
                "service_account_email is required "
                "for service-account credentials."
            )

        if (
            config.service_account_key_path is None
            or not config.service_account_key_path.strip()
        ):
            errors.append(
                "service_account_key_path is required "
                "for service-account credentials."
            )
        elif Path(config.service_account_key_path).suffix.lower() != ".json":
            errors.append(
                "service_account_key_path must reference a JSON file."
            )

    else:
        if config.service_account_email is not None:
            errors.append(
                "service_account_email is only valid "
                "for service-account credentials."
            )

        if config.service_account_key_path is not None:
            errors.append(
                "service_account_key_path is only valid "
                "for service-account credentials."
            )

    return tuple(errors)