from pathlib import Path

from geoai_dataset_curation.contracts import load_source_registry


def test_source_registry_loads_expected_records() -> None:
    registry_path = Path("registry/sources.yaml")

    records = load_source_registry(registry_path)

    assert len(records) == 4
    assert records[0].id == "padena_aoi"
    assert records[1].label_value == 1
    assert records[2].label_value == 0
    assert records[3].role == "hard_negative_reference"