"""Tests for ignore-aware binary segmentation metrics."""
import numpy as np
import pytest
from geoai_dataset_curation.evaluation_metrics import evaluate_labeled_pixels


def test_perfect_classification_excludes_ignored_pixels():
    labels = np.array([[1, 0], [255, 1]], dtype=np.uint8)
    probabilities = np.array([[0.9, 0.1], [0.99, 0.7]])
    result = evaluate_labeled_pixels(probabilities, labels)
    assert (result["tp"], result["tn"], result["fp"], result["fn"]) == (2, 1, 0, 0)
    assert result["ignored_pixels"] == 1
    assert result["positive_iou"] == 1.0
    assert result["f1"] == 1.0
    assert result["roc_auc"] == 1.0
    assert result["average_precision"] == 1.0


def test_confusion_and_ranking_metrics():
    labels = np.array([1, 1, 0, 0], dtype=np.uint8)
    probabilities = np.array([0.9, 0.4, 0.8, 0.1])
    result = evaluate_labeled_pixels(probabilities, labels)
    assert (result["tp"], result["tn"], result["fp"], result["fn"]) == (1, 1, 1, 1)
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["positive_iou"] == pytest.approx(1 / 3)
    assert result["roc_auc"] == 0.75
    assert result["average_precision"] == pytest.approx(5 / 6)


def test_constant_probabilities_handle_ties():
    labels = np.array([1, 0, 1, 0], dtype=np.uint8)
    probabilities = np.full(4, 0.2)
    result = evaluate_labeled_pixels(probabilities, labels)
    assert result["roc_auc"] == 0.5
    assert result["average_precision"] == 0.5
    assert result["precision"] is None
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0
    assert result["positive_iou"] == 0.0


def test_negative_only_split_has_undefined_positive_metrics():
    labels = np.array([0, 0], dtype=np.uint8)
    probabilities = np.array([0.1, 0.9])
    result = evaluate_labeled_pixels(probabilities, labels)
    assert result["fp"] == 1
    assert result["specificity"] == 0.5
    assert result["recall"] is None
    assert result["f1"] is None
    assert result["positive_iou"] is None
    assert result["roc_auc"] is None
    assert result["average_precision"] is None


def test_threshold_is_inclusive():
    result = evaluate_labeled_pixels(
        np.array([0.5, 0.49]),
        np.array([1, 0]),
    )
    assert result["tp"] == 1
    assert result["tn"] == 1


@pytest.mark.parametrize(
    "scores,labels,threshold",
    [
        ([0.1], [255], 0.5),
        ([0.1], [2], 0.5),
        ([float("nan")], [0], 0.5),
        ([1.1], [0], 0.5),
        ([0.3], [0, 1], 0.5),
        ([0.3], [0], 1.0),
    ],
)
def test_invalid_inputs_are_rejected(scores, labels, threshold):
    with pytest.raises(ValueError):
        evaluate_labeled_pixels(
            np.array(scores),
            np.array(labels),
            threshold=threshold,
        )