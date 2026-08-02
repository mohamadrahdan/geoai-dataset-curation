"Configuration contracts for Earth Engine initialization"
from dataclasses import dataclass
from enum import StrEnum


class EarthEngineCredentialSource(StrEnum):
    "Supported credential sources for Earth Engine initialization"
    PERSISTENT = "persistent"
    APPLICATION_DEFAULT = "application_default"
    SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True)
class EarthEngineConfig:
    "Configuration required to authenticate and initialize Earth Engine"
    project_id: str
    credential_source: EarthEngineCredentialSource
    service_account_email: str | None = None
    service_account_key_path: str | None = None
    api_endpoint: str | None = None