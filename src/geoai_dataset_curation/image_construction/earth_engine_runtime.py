"Runtime boundary for Earth Engine initialization"
from typing import Protocol, runtime_checkable


@runtime_checkable
class EarthEngineRuntime(Protocol):
    "SDK-neutral boundary for initializing Earth Engine"
    def initialize_with_persistent_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize using credentials stored for the local user"
        ...

    def initialize_with_application_default_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize using application-default credentials"
        ...

    def initialize_with_service_account_credentials(
        self,
        *,
        project_id: str,
        service_account_email: str,
        service_account_key_path: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize using explicit service-account credentials"
        ...