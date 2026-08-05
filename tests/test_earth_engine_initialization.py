from dataclasses import dataclass, field
from geoai_dataset_curation.image_construction import (
    EarthEngineConfig,
    EarthEngineCredentialSource,
    EarthEngineInitializationResult,
    EarthEngineRuntime,
    initialize_earth_engine,
)


@dataclass
class FakeEarthEngineRuntime:
    "Record Earth Engine initialization calls for tests"
    calls: list[tuple[str, dict[str, str | None]]] = field(
        default_factory=list
    )

    def initialize_with_persistent_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        self.calls.append(
            (
                "persistent",
                {
                    "project_id": project_id,
                    "api_endpoint": api_endpoint,
                },
            )
        )

    def initialize_with_application_default_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        self.calls.append(
            (
                "application_default",
                {
                    "project_id": project_id,
                    "api_endpoint": api_endpoint,
                },
            )
        )

    def initialize_with_service_account_credentials(
        self,
        *,
        project_id: str,
        service_account_email: str,
        service_account_key_path: str,
        api_endpoint: str | None,
    ) -> None:
        self.calls.append(
            (
                "service_account",
                {
                    "project_id": project_id,
                    "service_account_email": (
                        service_account_email
                    ),
                    "service_account_key_path": (
                        service_account_key_path
                    ),
                    "api_endpoint": api_endpoint,
                },
            )
        )


def test_fake_runtime_satisfies_runtime_protocol() -> None:
    runtime = FakeEarthEngineRuntime()
    assert isinstance(runtime, EarthEngineRuntime)


def test_initialize_earth_engine_uses_persistent_credentials() -> None:
    runtime = FakeEarthEngineRuntime()
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )

    result = initialize_earth_engine(
        config=config,
        runtime=runtime,
    )
    assert runtime.calls == [
        (
            "persistent",
            {
                "project_id": "padena-geoai",
                "api_endpoint": None,
            },
        )
    ]
    assert result == EarthEngineInitializationResult(
        project_id="padena-geoai",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
        api_endpoint=None,
    )


def test_initialize_earth_engine_uses_application_default_credentials() -> None:
    runtime = FakeEarthEngineRuntime()
    config = EarthEngineConfig(
        project_id="padena-geoai",
        credential_source=(
            EarthEngineCredentialSource.APPLICATION_DEFAULT
        ),
        api_endpoint="https://earthengine.googleapis.com",
    )

    result = initialize_earth_engine(
        config=config,
        runtime=runtime,
    )
    assert runtime.calls == [
        (
            "application_default",
            {
                "project_id": "padena-geoai",
                "api_endpoint": (
                    "https://earthengine.googleapis.com"
                ),
            },
        )
    ]
    assert result.credential_source is (
        EarthEngineCredentialSource.APPLICATION_DEFAULT
    )


def test_initialize_earth_engine_uses_service_account_credentials() -> None:
    runtime = FakeEarthEngineRuntime()
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

    result = initialize_earth_engine(
        config=config,
        runtime=runtime,
    )
    assert runtime.calls == [
        (
            "service_account",
            {
                "project_id": "padena-geoai",
                "service_account_email": (
                    "geoai-runner@padena-geoai."
                    "iam.gserviceaccount.com"
                ),
                "service_account_key_path": (
                    "secrets/earth-engine-key.json"
                ),
                "api_endpoint": None,
            },
        )
    ]
    assert result.credential_source is (
        EarthEngineCredentialSource.SERVICE_ACCOUNT
    )


def test_initialize_earth_engine_validates_before_runtime_call() -> None:
    runtime = FakeEarthEngineRuntime()
    config = EarthEngineConfig(
        project_id=" ",
        credential_source=EarthEngineCredentialSource.PERSISTENT,
    )

    try:
        initialize_earth_engine(
            config=config,
            runtime=runtime,
        )
    except ValueError as error:
        assert (
            "Cannot build Earth Engine credential strategy"
            in str(error)
        )
    else:
        raise AssertionError("Expected invalid configuration to fail.")
    assert runtime.calls == []