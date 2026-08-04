import pytest
from geoai_dataset_curation.image_construction import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
    EarthEngineCredentialStrategy,
    build_earth_engine_credential_strategy,
)


def test_persistent_strategy_allows_interactive_authentication() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )

    strategy = build_earth_engine_credential_strategy(config)
    assert strategy == EarthEngineCredentialStrategy(
        credential_source=EarthEngineCredentialSource.PERSISTENT,
        uses_explicit_credentials=False,
        allows_interactive_authentication=True,
    )


def test_application_default_strategy_uses_environment_credentials() -> None:
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=(
            EarthEngineCredentialSource.APPLICATION_DEFAULT
        ),
    )

    strategy = build_earth_engine_credential_strategy(config)
    assert strategy == EarthEngineCredentialStrategy(
        credential_source=(
            EarthEngineCredentialSource.APPLICATION_DEFAULT
        ),
        uses_explicit_credentials=False,
        allows_interactive_authentication=False,
    )


def test_service_account_strategy_uses_explicit_credentials() -> None:
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

    strategy = build_earth_engine_credential_strategy(config)
    assert strategy == EarthEngineCredentialStrategy(
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
        uses_explicit_credentials=True,
        allows_interactive_authentication=False,
        service_account_email=(
            "geoai-runner@padena-geoai.iam.gserviceaccount.com"
        ),
        service_account_key_path=(
            "secrets/earth-engine-key.json"
        ),
    )


def test_credential_strategy_rejects_invalid_configuration() -> None:
    config = EarthEngineConfig(
        project_id=" ",
        credential_source=EarthEngineCredentialSource.SERVICE_ACCOUNT,
    )

    with pytest.raises(
        ValueError,
        match="Cannot build Earth Engine credential strategy",
    ):
        build_earth_engine_credential_strategy(config)