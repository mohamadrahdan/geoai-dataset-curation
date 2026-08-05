import pytest
from geoai_dataset_curation.image_construction import (
    API_ENDPOINT_ENV,
    CREDENTIAL_SOURCE_ENV,
    PROJECT_ID_ENV,
    SERVICE_ACCOUNT_EMAIL_ENV,
    SERVICE_ACCOUNT_KEY_PATH_ENV,
    EarthEngineCredentialSource,
    load_earth_engine_config,
)


def test_load_earth_engine_config_uses_persistent_credentials_by_default() -> None:
    config = load_earth_engine_config(
        {
            PROJECT_ID_ENV: "padena-geoai",
        }
    )

    assert config.project_id == "padena-geoai"
    assert (
        config.credential_source
        is EarthEngineCredentialSource.PERSISTENT
    )
    assert config.service_account_email is None
    assert config.service_account_key_path is None
    assert config.api_endpoint is None


def test_load_earth_engine_config_loads_application_default_credentials() -> None:
    config = load_earth_engine_config(
        {
            PROJECT_ID_ENV: "padena-geoai",
            CREDENTIAL_SOURCE_ENV: "application_default",
            API_ENDPOINT_ENV: "https://earthengine.googleapis.com",
        }
    )

    assert (
        config.credential_source
        is EarthEngineCredentialSource.APPLICATION_DEFAULT
    )
    assert (
        config.api_endpoint
        == "https://earthengine.googleapis.com"
    )


def test_load_earth_engine_config_loads_service_account_settings() -> None:
    config = load_earth_engine_config(
        {
            PROJECT_ID_ENV: "padena-geoai",
            CREDENTIAL_SOURCE_ENV: "service_account",
            SERVICE_ACCOUNT_EMAIL_ENV: (
                "geoai-runner@padena-geoai.iam.gserviceaccount.com"
            ),
            SERVICE_ACCOUNT_KEY_PATH_ENV: (
                "secrets/earth-engine-key.json"
            ),
        }
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


def test_load_earth_engine_config_strips_environment_values() -> None:
    config = load_earth_engine_config(
        {
            PROJECT_ID_ENV: "  padena-geoai  ",
            CREDENTIAL_SOURCE_ENV: " persistent ",
            API_ENDPOINT_ENV: "  ",
        }
    )

    assert config.project_id == "padena-geoai"
    assert config.api_endpoint is None


def test_load_earth_engine_config_preserves_empty_project_for_validation() -> None:
    config = load_earth_engine_config({})

    assert config.project_id == ""
    assert (
        config.credential_source
        is EarthEngineCredentialSource.PERSISTENT
    )


def test_load_earth_engine_config_rejects_unknown_credential_source() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "GEOAI_EE_CREDENTIAL_SOURCE must be one of"
        ),
    ):
        load_earth_engine_config(
            {
                PROJECT_ID_ENV: "padena-geoai",
                CREDENTIAL_SOURCE_ENV: "unknown",
            }
        )


def test_load_earth_engine_config_can_read_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PROJECT_ID_ENV, "padena-geoai")
    monkeypatch.setenv(
        CREDENTIAL_SOURCE_ENV,
        "application_default",
    )

    config = load_earth_engine_config()

    assert config.project_id == "padena-geoai"
    assert (
        config.credential_source
        is EarthEngineCredentialSource.APPLICATION_DEFAULT
    )