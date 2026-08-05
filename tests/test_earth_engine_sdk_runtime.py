from dataclasses import dataclass, field
from typing import Any
import pytest
from requests.exceptions import ConnectionError
from geoai_dataset_curation.image_construction import (
    EarthEngineAuthenticationError,
    EarthEngineConnectionError,
    EarthEngineRuntime,
    EarthEngineSdkRuntime,
)


@dataclass
class FakeEarthEngineSdk:
    "Record calls made through the concrete SDK adapter"
    initialize_calls: list[dict[str, Any]] = field(
        default_factory=list
    )
    service_account_calls: list[tuple[str, str]] = field(
        default_factory=list
    )
    initialize_error: Exception | None = None
    service_account_error: Exception | None = None

    def Initialize(self, **arguments: Any) -> None:
        if self.initialize_error is not None:
            raise self.initialize_error

        self.initialize_calls.append(arguments)

    def ServiceAccountCredentials(
        self,
        email: str,
        key_path: str,
    ) -> object:
        if self.service_account_error is not None:
            raise self.service_account_error

        self.service_account_calls.append((email, key_path))
        return {
            "email": email,
            "key_path": key_path,
        }


def test_sdk_runtime_satisfies_runtime_protocol() -> None:
    runtime = EarthEngineSdkRuntime(
        sdk=FakeEarthEngineSdk(),
    )
    assert isinstance(runtime, EarthEngineRuntime)


def test_sdk_runtime_initializes_with_persistent_credentials() -> None:
    sdk = FakeEarthEngineSdk()
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    runtime.initialize_with_persistent_credentials(
        project_id="padena-geoai",
        api_endpoint=None,
    )
    assert sdk.initialize_calls == [
        {
            "credentials": "persistent",
            "project": "padena-geoai",
        }
    ]


def test_sdk_runtime_passes_custom_endpoint() -> None:
    sdk = FakeEarthEngineSdk()
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    runtime.initialize_with_persistent_credentials(
        project_id="padena-geoai",
        api_endpoint=(
            "https://earthengine-highvolume.googleapis.com"
        ),
    )
    assert sdk.initialize_calls == [
        {
            "credentials": "persistent",
            "project": "padena-geoai",
            "opt_url": (
                "https://earthengine-highvolume.googleapis.com"
            ),
        }
    ]


def test_sdk_runtime_uses_application_default_credentials() -> None:
    sdk = FakeEarthEngineSdk()
    credentials = object()

    def load_credentials() -> tuple[object, str | None]:
        return credentials, "detected-project"

    runtime = EarthEngineSdkRuntime(
        sdk=sdk,
        application_default_credentials_loader=load_credentials,
    )

    runtime.initialize_with_application_default_credentials(
        project_id="padena-geoai",
        api_endpoint=None,
    )
    assert sdk.initialize_calls == [
        {
            "credentials": credentials,
            "project": "padena-geoai",
        }
    ]


def test_sdk_runtime_builds_service_account_credentials() -> None:
    sdk = FakeEarthEngineSdk()
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    runtime.initialize_with_service_account_credentials(
        project_id="padena-geoai",
        service_account_email=(
            "geoai-runner@padena-geoai.iam.gserviceaccount.com"
        ),
        service_account_key_path=(
            "secrets/earth-engine-key.json"
        ),
        api_endpoint=None,
    )
    assert sdk.service_account_calls == [
        (
            "geoai-runner@padena-geoai.iam.gserviceaccount.com",
            "secrets/earth-engine-key.json",
        )
    ]
    assert sdk.initialize_calls == [
        {
            "credentials": {
                "email": (
                    "geoai-runner@padena-geoai."
                    "iam.gserviceaccount.com"
                ),
                "key_path": (
                    "secrets/earth-engine-key.json"
                ),
            },
            "project": "padena-geoai",
        }
    ]


def test_sdk_runtime_normalizes_initialization_failure() -> None:
    sdk = FakeEarthEngineSdk(
        initialize_error=RuntimeError("invalid credentials"),
    )
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    with pytest.raises(
        EarthEngineAuthenticationError,
        match="Earth Engine initialization failed",
    ):
        runtime.initialize_with_persistent_credentials(
            project_id="padena-geoai",
            api_endpoint=None,
        )


def test_sdk_runtime_normalizes_connection_failure() -> None:
    sdk = FakeEarthEngineSdk(
        initialize_error=ConnectionError("network unavailable"),
    )
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    with pytest.raises(
        EarthEngineConnectionError,
        match="Earth Engine could not be reached",
    ):
        runtime.initialize_with_persistent_credentials(
            project_id="padena-geoai",
            api_endpoint=None,
        )


def test_sdk_runtime_normalizes_adc_loading_failure() -> None:
    sdk = FakeEarthEngineSdk()

    def fail_to_load_credentials() -> tuple[object, str | None]:
        raise RuntimeError("credentials unavailable")

    runtime = EarthEngineSdkRuntime(
        sdk=sdk,
        application_default_credentials_loader=(
            fail_to_load_credentials
        ),
    )

    with pytest.raises(
        EarthEngineAuthenticationError,
        match="Application Default Credentials could not be loaded",
    ):
        runtime.initialize_with_application_default_credentials(
            project_id="padena-geoai",
            api_endpoint=None,
        )

    assert sdk.initialize_calls == []


def test_sdk_runtime_normalizes_key_file_failure() -> None:
    sdk = FakeEarthEngineSdk(
        service_account_error=OSError("file not found"),
    )
    runtime = EarthEngineSdkRuntime(sdk=sdk)

    with pytest.raises(
        EarthEngineAuthenticationError,
        match="service-account key file could not be read",
    ):
        runtime.initialize_with_service_account_credentials(
            project_id="padena-geoai",
            service_account_email=(
                "geoai-runner@padena-geoai."
                "iam.gserviceaccount.com"
            ),
            service_account_key_path=(
                "missing-key.json"
            ),
            api_endpoint=None,
        )

    assert sdk.initialize_calls == []