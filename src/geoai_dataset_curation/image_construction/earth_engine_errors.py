"Normalized errors for the Earth Engine provider boundary"

class EarthEngineProviderError(RuntimeError):
    "Base error raised by Earth Engine provider implementations"


class EarthEngineConnectionError(EarthEngineProviderError):
    "Raised when the provider cannot communicate with Earth Engine"


class EarthEngineAuthenticationError(EarthEngineProviderError):
    "Raised when Earth Engine authentication or initialization fails"


class EarthEngineRequestError(EarthEngineProviderError):
    "Raised when Earth Engine rejects or cannot process a request"


class EarthEngineExportError(EarthEngineProviderError):
    "Raised when an Earth Engine export cannot be started or completed"