from geoai_dataset_curation.contracts import LabelValue


def test_label_values_match_contract() -> None:
    assert LabelValue.BACKGROUND == 0
    assert LabelValue.LANDSLIDE == 1
    assert LabelValue.IGNORE == 255