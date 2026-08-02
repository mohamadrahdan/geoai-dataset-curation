from geoai_dataset_curation.image_construction import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
)


def test_earth_engine_config_stores_persistent_credentials_settings() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )
    assert config.project_id == "padena-geoai"
    assert (
        config.credential_source
        is EarthEngineCredentialSource.PERSISTENT
    )
    assert config.service_account_email is None
    assert config.service_account_key_path is None
    assert config.api_endpoint is None


def test_earth_engine_config_stores_application_default_settings() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=(
            EarthEngineCredentialSource.APPLICATION_DEFAULT
        ),
    )
    assert (
        config.credential_source
        is EarthEngineCredentialSource.APPLICATION_DEFAULT
    )


def test_earth_engine_config_stores_service_account_settings() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
        service_account_email="geoai-runner@padena-geoai.iam.gserviceaccount.com",
        service_account_key_path="secrets/earth-engine-key.json",
    )

    assert (
        config.credential_source
        is EarthEngineCredentialSource.SERVICE_ACCOUNT
    )
    assert config.service_account_email == (
        "geoai-runner@padena-geoai.iam.gserviceaccount.com"
    )
    assert (
        config.service_account_key_path
        == "secrets/earth-engine-key.json"
    )


def test_earth_engine_config_accepts_custom_api_endpoint() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
        api_endpoint="https://earthengine.googleapis.com",
    )
    assert (
        config.api_endpoint
        == "https://earthengine.googleapis.com"
    )