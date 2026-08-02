import pytest
from geoai_dataset_curation.image_construction import (
    EarthEngineAuthenticationError,
    EarthEngineConnectionError,
    EarthEngineExportError,
    EarthEngineProviderError,
    EarthEngineRequestError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        EarthEngineAuthenticationError,
        EarthEngineConnectionError,
        EarthEngineRequestError,
        EarthEngineExportError,
    ],
)
def test_specific_earth_engine_errors_inherit_from_provider_error(
    error_type: type[EarthEngineProviderError],
) -> None:
    error = error_type("simulated failure")

    assert isinstance(error, EarthEngineProviderError)
    assert isinstance(error, RuntimeError)
    assert str(error) == "simulated failure"


def test_provider_error_can_be_caught_through_common_boundary() -> None:
    with pytest.raises(
        EarthEngineProviderError,
        match="authentication failed",
    ):
        raise EarthEngineAuthenticationError(
            "authentication failed"
        )