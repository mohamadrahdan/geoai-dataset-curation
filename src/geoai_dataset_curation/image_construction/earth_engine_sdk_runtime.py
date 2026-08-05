"Concrete Earth Engine runtime backed by the Python SDK"
from collections.abc import Callable
from typing import Any
import ee
import google.auth
from google.auth.exceptions import (
    DefaultCredentialsError,
    RefreshError,
)
from requests.exceptions import RequestException
from geoai_dataset_curation.image_construction.earth_engine_errors import (
    EarthEngineAuthenticationError,
    EarthEngineConnectionError,
)


ApplicationDefaultCredentialsLoader = Callable[
    [],
    tuple[Any, str | None],
]


class EarthEngineSdkRuntime:
    "Initialize Earth Engine through the real Python SDK"
    def __init__(
        self,
        *,
        sdk: Any = ee,
        application_default_credentials_loader: (
            ApplicationDefaultCredentialsLoader
        ) = google.auth.default,
    ) -> None:
        self._sdk = sdk
        self._application_default_credentials_loader = (
            application_default_credentials_loader
        )

    def initialize_with_persistent_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize with credentials stored for the local user"
        self._initialize(
            credentials="persistent",
            project_id=project_id,
            api_endpoint=api_endpoint,
        )

    def initialize_with_application_default_credentials(
        self,
        *,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize with Application Default Credentials"
        try:
            credentials, _ = (
                self._application_default_credentials_loader()
            )
        except (DefaultCredentialsError, RefreshError) as error:
            raise EarthEngineAuthenticationError(
                "Application Default Credentials could not be loaded."
            ) from error
        except RequestException as error:
            raise EarthEngineConnectionError(
                "Application Default Credentials could not be reached."
            ) from error
        except Exception as error:
            raise EarthEngineAuthenticationError(
                "Application Default Credentials could not be loaded."
            ) from error

        self._initialize(
            credentials=credentials,
            project_id=project_id,
            api_endpoint=api_endpoint,
        )

    def initialize_with_service_account_credentials(
        self,
        *,
        project_id: str,
        service_account_email: str,
        service_account_key_path: str,
        api_endpoint: str | None,
    ) -> None:
        "Initialize with an explicit service-account key"
        try:
            credentials = self._sdk.ServiceAccountCredentials(
                service_account_email,
                service_account_key_path,
            )
        except (DefaultCredentialsError, RefreshError) as error:
            raise EarthEngineAuthenticationError(
                "Service-account credentials could not be created."
            ) from error
        except OSError as error:
            raise EarthEngineAuthenticationError(
                "The service-account key file could not be read."
            ) from error
        except Exception as error:
            raise EarthEngineAuthenticationError(
                "Service-account credentials could not be created."
            ) from error

        self._initialize(
            credentials=credentials,
            project_id=project_id,
            api_endpoint=api_endpoint,
        )

    def _initialize(
        self,
        *,
        credentials: Any,
        project_id: str,
        api_endpoint: str | None,
    ) -> None:
        "Call the SDK and normalize initialization failures"
        arguments: dict[str, Any] = {
            "credentials": credentials,
            "project": project_id,
        }

        if api_endpoint is not None:
            arguments["opt_url"] = api_endpoint

        try:
            self._sdk.Initialize(**arguments)
        except RequestException as error:
            raise EarthEngineConnectionError(
                "Earth Engine could not be reached during initialization."
            ) from error
        except (DefaultCredentialsError, RefreshError) as error:
            raise EarthEngineAuthenticationError(
                "Earth Engine credentials were rejected."
            ) from error
        except Exception as error:
            raise EarthEngineAuthenticationError(
                "Earth Engine initialization failed."
            ) from error