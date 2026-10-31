"Pixel-level metrics for binary segmentation with ignored labels."
import numpy as np


def _roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores, kind="stable")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    starts = np.r_[0, np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]) + 1]
    ends = np.r_[starts[1:], len(scores)]
    counts = np.add.reduceat(sorted_labels.astype(np.int64), starts)
    average_ranks = (starts + 1 + ends) / 2.0

    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    rank_sum = float(np.sum(counts * average_ranks))

    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(-scores, kind="stable")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    ends = np.r_[np.flatnonzero(sorted_scores[:-1] != sorted_scores[1:]), len(scores) - 1]
    tp = np.cumsum(sorted_labels, dtype=np.int64)[ends]
    precision = tp / (ends + 1)
    recall_step = np.diff(np.r_[0, tp]) / int(labels.sum())

    return float(np.sum(precision * recall_step))


def evaluate_labeled_pixels(
    probabilities: np.ndarray,
    labels: np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, int | float | None]:
    "Evaluate binary predictions using only labels 0 and 1."
    scores = np.asarray(probabilities)
    masks = np.asarray(labels)

    if scores.shape != masks.shape or scores.size == 0:
        raise ValueError("Probabilities and labels must have identical nonempty shapes.")
    if not np.issubdtype(scores.dtype, np.number) or np.iscomplexobj(scores):
        raise ValueError("Probabilities must be real numeric values.")
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("Probabilities must be finite and within [0, 1].")
    if not np.isin(masks, (0, 1, 255)).all():
        raise ValueError("Labels must contain only 0, 1, or 255.")
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Threshold must be finite and strictly between 0 and 1.")

    valid = masks != 255

    if not np.any(valid):
        raise ValueError("No supervised pixels are available for evaluation.")
    y = masks[valid].astype(np.uint8)
    p = scores[valid].astype(np.float64)

    predicted = p >= threshold
    positive = y == 1
    negative = ~positive

    tp = int(np.count_nonzero(predicted & positive))
    tn = int(np.count_nonzero(~predicted & negative))
    fp = int(np.count_nonzero(predicted & negative))
    fn = int(np.count_nonzero(~predicted & positive))

    n_pos = tp + fn
    n_neg = tn + fp
    n_valid = len(y)

    has_both_classes = n_pos > 0 and n_neg > 0

    return {
        "threshold": float(threshold),
        "valid_pixels": n_valid,
        "ignored_pixels": int(masks.size - n_valid),
        "positive_pixels": n_pos,
        "negative_pixels": n_neg,
        "positive_prevalence": n_pos / n_valid,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": (tp + tn) / n_valid,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / n_pos if n_pos else None,
        "specificity": tn / n_neg if n_neg else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if n_pos else None,
        "positive_iou": tp / (tp + fp + fn) if n_pos else None,
        "roc_auc": _roc_auc(y, p) if has_both_classes else None,
        "average_precision": _average_precision(y, p) if has_both_classes else None,
    }