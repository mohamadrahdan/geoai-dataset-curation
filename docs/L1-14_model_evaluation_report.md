# L1-14 — Frozen Baseline Model Evaluation Report

## Objective

Evaluate the frozen Padena landslide segmentation baseline on the
held-out test split using a predefined evaluation protocol.

The purpose is independent performance measurement, not model
optimization or threshold selection.

## 1. Evaluation Configuration

- Dataset: padena_dataset_v1.0.0
- Model: padena_model_v1.0.0
- Architecture: Small U-Net
- Activation: LeakyReLU
- Input: Sentinel-2 bands B2, B3, B4, B8
- Training loss: Unweighted masked BCE
- Training epochs: 10
- Checkpoint: Final epoch
- Evaluation split: test
- Decision threshold: 0.5
- Aggregation: Global pixel-level (micro)
- Ignore label: 255

Model and dataset SHA-256 fingerprints were verified before inference.
Their exact values are recorded in the machine-readable evaluation report.

## 2. Test Dataset

| Property | Value |
|---|---:|
| Test tiles | 13 |
| Positive-labeled tiles | 11 |
| Negative-only tiles | 2 |
| Valid labeled pixels | 19,067 |
| Positive pixels | 14,941 |
| Verified negative pixels | 4,126 |
| Ignored pixels | 832,901 |
| Positive prevalence among valid pixels | 78.36% |
| Ignored proportion of all test pixels | 97.76% |

Only verified positive and negative labels were evaluated.

## 3. Global Confusion Matrix

| Ground truth | Predicted positive | Predicted negative |
|---|---:|---:|
| Positive | 0 | 14,941 |
| Negative | 1 | 4,125 |

The model predicted only one positive pixel, which was a false positive.

## 4. Evaluation Metrics

| Metric | Result |
|---|---:|
| Precision | 0.000000 |
| Recall | 0.000000 |
| F1 | 0.000000 |
| Positive IoU | 0.000000 |
| Specificity | 0.999758 |
| Accuracy | 0.216342 |
| ROC-AUC | 0.531839 |
| Average Precision | 0.799901 |

All metrics were computed on valid labeled pixels only.

## 5. Interpretation

At the predefined threshold of 0.5, the model failed to identify
any positive landslide pixels.

High specificity is not evidence of successful segmentation because
the model predicted nearly every valid pixel as negative.

ROC-AUC was close to 0.5, indicating weak class-ranking ability.

Average Precision must be interpreted relative to the positive
prevalence of approximately 0.783605. The observed AP of 0.799901
is only about 0.0163 higher than this reference.

These findings do not support reliable landslide detection
performance for the selected baseline.

## 6. Dataset and Evaluation Limitations

The training and test splits have substantially different positive
class prevalence among labeled pixels:

- Train: approximately 10.36%
- Test: approximately 78.36%

This difference complicates interpretation and comparison.

The test set contains only 13 tiles, and approximately 97.76%
of its pixels are excluded because they lack valid labels.

Pixel observations are spatially dependent and should not be
interpreted as independent experimental samples.

The validation split contains no positive-labeled pixels and
cannot establish positive-class recall or IoU.

These limitations restrict the scope of conclusions that can be
drawn from the reported metrics.

## 7. Test Integrity

The model checkpoint and decision threshold were fixed before
the first test evaluation.

The evaluation procedure used the frozen test split without
retraining, checkpoint reselection, or post-test threshold tuning.

The results are reported as observed, including zero positive
detection performance.

The test split must not subsequently be used to optimize this
model while retaining claims of independent evaluation.

## 8. Engineering Verification

- Evaluation metric tests: 11 passed
- Evaluation runner tests: 6 passed
- Complete repository test suite: 664 passed
- Model checkpoint integrity: Verified
- Dataset manifest integrity: Verified
- Train smoke evaluation: Passed
- Frozen test execution: Completed

The evaluation report includes global metrics, per-tile metrics,
model and dataset identifiers, and cryptographic fingerprints.

## 9. Artifacts

Model:

artifacts/models/padena_model_v1.0.0/

Machine-readable evaluation report:

artifacts/evaluations/padena_model_v1.0.0_test_v1.json

These local artifacts are excluded from Git and must be
preserved separately.

Evaluation report SHA-256:
445d9158e86a64ae725ca5350bf79dcf427134a93264a4fccbba020ad418ab10

## 10. Conclusion

L1-14 successfully established and executed a reproducible,
traceable, ignore-aware evaluation procedure.

The engineering evaluation workflow is functional.

However, the frozen baseline did not demonstrate useful
positive-class segmentation at the predefined threshold.

This distinction between engineering correctness and scientific
model performance is an explicit outcome of the project.

Any future improvements to dataset composition, training
strategy, or model architecture must be treated as a new
development cycle with an appropriate independent evaluation
protocol.