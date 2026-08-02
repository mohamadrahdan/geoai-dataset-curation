from geoai_dataset_curation.image_construction import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
    validate_earth_engine_config,
)


def test_validate_earth_engine_config_accepts_persistent_credentials() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )
    errors = validate_earth_engine_config(config)
    assert errors == ()


def test_validate_earth_engine_config_accepts_application_default_credentials() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=(
            EarthEngineCredentialSource.APPLICATION_DEFAULT
        ),
        api_endpoint="https://earthengine.googleapis.com",
    )
    errors = validate_earth_engine_config(config)
    assert errors == ()


def test_validate_earth_engine_config_accepts_service_account_credentials() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
        service_account_email=(
            "geoai-runner@padena-geoai.iam.gserviceaccount.com"
        ),
        service_account_key_path=(
            "secrets/earth-engine-key.json"
        ),
    )
    errors = validate_earth_engine_config(config)
    assert errors == ()


def test_validate_earth_engine_config_rejects_empty_project_id() -> None:
    config = EarthEngineConfig(
        project_id=" ",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )
    errors = validate_earth_engine_config(config)
    assert "project_id must not be empty." in errors


def test_validate_earth_engine_config_rejects_invalid_api_endpoint() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
        api_endpoint="http://earthengine.googleapis.com",
    )
    errors = validate_earth_engine_config(config)
    assert (
        "api_endpoint must be an absolute HTTPS URL."
        in errors
    )


def test_validate_earth_engine_config_requires_service_account_fields() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
    )
    errors = validate_earth_engine_config(config)
    assert (
        "service_account_email is required "
        "for service-account credentials."
        in errors
    )
    assert (
        "service_account_key_path is required "
        "for service-account credentials."
        in errors
    )


def test_validate_earth_engine_config_requires_json_key_file() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
        service_account_email=(
            "geoai-runner@padena-geoai.iam.gserviceaccount.com"
        ),
        service_account_key_path="secrets/earth-engine-key.txt",
    )
    errors = validate_earth_engine_config(config)
    assert (
        "service_account_key_path must reference a JSON file."
        in errors
    )


def test_validate_earth_engine_config_rejects_service_account_fields_for_other_sources() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
        service_account_email="unexpected@example.com",
        service_account_key_path="unexpected.json",
    )
    errors = validate_earth_engine_config(config)
    assert (
        "service_account_email is only valid "
        "for service-account credentials."
        in errors
    )
    assert (
        "service_account_key_path is only valid "
        "for service-account credentials."
        in errors
    )