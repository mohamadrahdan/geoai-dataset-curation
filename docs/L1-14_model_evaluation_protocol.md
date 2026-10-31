# L1-14 — Model Evaluation Protocol

## Objective

Evaluate the frozen engineering baseline independently and report its performance without post-test model selection or threshold tuning.

## 1. Frozen model

Selected artifact: `artifacts/models/padena_model_v1.0.0/`

- Architecture: Small U-Net
- Input channels: B2, B3, B4, B8
- Activation: LeakyReLU
- Training loss: Unweighted masked BCE
- Training epochs: 10
- Checkpoint policy: Final epoch
- Source release: padena_dataset_v1.0.0

The checkpoint SHA-256 must match its stored metadata.

The dataset manifest SHA-256 must also match the value recorded in the model metadata.

Exact artifact fingerprints must be recorded in the evaluation report.

No model retraining or checkpoint reselection is permitted after test evaluation.

## 2. Fixed decision rule

The binary decision threshold is 0.5.

Predicted positive: probability >= 0.5.

Predicted negative: probability < 0.5.

The threshold is fixed before accessing the test split.

## 3. Label semantics

- 0: Verified negative
- 1: Landslide
- 255: Ignore / unlabeled

Only pixels labeled 0 or 1 contribute to evaluation.

Ignored pixels are not treated as negatives.

## 4. Metrics

Threshold-dependent metrics:

- TP, TN, FP, FN
- Precision
- Recall
- Specificity
- F1
- Positive-class IoU
- Accuracy (secondary only)

Threshold-independent ranking metrics:

- ROC-AUC
- Average Precision (AP)

AP is not reported as trapezoidal PR-AUC.

ROC-AUC and AP are undefined when either ground-truth class is absent.

Positive-class Recall, F1, and IoU are undefined when no positive ground-truth pixels exist.

Precision is undefined when no positive predictions exist.

Undefined values must be stored as null, not fabricated zeros.

## 5. Aggregation

Primary results are calculated globally across all valid test pixels.

Confusion counts are summed over samples before calculating global classification metrics.

ROC-AUC and AP are calculated using all valid test-pixel scores together.

Per-tile results are reported separately as diagnostics.

The mean of per-tile metrics must not replace the global result.

## 6. Validation limitation

The frozen validation split contains no positive-labeled samples.

It cannot independently establish positive-class Recall, F1, or IoU.

No positive-class threshold optimization will be performed using this split.

## 7. Test-set policy

Test evaluation is performed only after:

1. Metric implementation and unit tests are complete.
2. The model artifact and checksums are verified.
3. The evaluation protocol is committed.
4. The evaluation runner has passed synthetic-data checks.

The frozen test split must not guide architecture, training, threshold, or checkpoint selection.

If performance is weak, it must be reported without post-test adjustment.

## 8. Reporting

The final report must contain:

- Dataset version and manifest fingerprint
- Model version and checkpoint fingerprint
- Fixed threshold and label contract
- Valid, ignored, positive, and negative pixel counts
- Global confusion matrix
- Global classification and ranking metrics
- Per-tile diagnostic metrics
- Undefined metric explanations
- Scientific limitations and interpretation

## 9. Interpretation limits

Pixel-level results do not independently measure object-level detection.

Spatial dependence, sample size, class imbalance, and label coverage must be discussed.

Results describe this frozen model and this specific held-out dataset only.

No production-readiness claim is implied.