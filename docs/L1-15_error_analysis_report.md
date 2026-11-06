# L1-15 — Baseline Error Analysis

## Objective

Diagnose the failure modes of the frozen Padena baseline without
retraining, changing the decision threshold, or selecting a new model.

This phase provides evidence for the Loop 2 development decision.

## 1. Frozen Baseline

- Dataset: padena_dataset_v1.0.0
- Model: padena_model_v1.0.0
- Architecture: Small U-Net, LeakyReLU
- Decision threshold: 0.5
- Test tiles: 13
- Positive IoU: 0.000
- F1: 0.000
- ROC-AUC: 0.531839
- Average Precision: 0.799901

The original frozen test evaluation remains unchanged.

## 2. Data and Label Findings

| Property | Train | Validation | Test |
|---|---:|---:|---:|
| Tiles | 33 | 4 | 13 |
| Positive tiles | 8 | 0 | 11 |
| Valid label coverage | 5.17% | 4.68% | 2.24% |
| Positive prevalence among valid pixels | 10.36% | 0.00% | 78.36% |

Findings:

- Valid supervision covers only a small fraction of the raster pixels.
- Validation contains no positive labels.
- Positive prevalence differs substantially between train and test.
- The dataset contains only three connected spatial groups.

These are confirmed dataset limitations, not proven causes of model failure.

## 3. Probability Diagnostics

| Statistic | Positive labels | Negative labels |
|---|---:|---:|
| Pixels | 14,941 | 4,126 |
| Mean probability | 0.10601 | 0.10295 |
| Median probability | 0.09252 | 0.09200 |
| Maximum probability | 0.49829 | 0.50810 |

The model produces very similar probabilities for both labeled classes.

No valid positive pixel exceeds the predefined 0.5 threshold.

## 4. Spatial Prediction Pattern

Across all 13 test tiles, exactly two pixels per tile were predicted
positive, always at the same local coordinates:

- (row=0, column=0)
- (row=0, column=255)

Of the 26 predicted-positive pixels:

- 0 corresponded to verified positive labels.
- 1 corresponded to a verified negative label.
- 25 had ignored labels.

All 13 tiles displayed the same coordinate pattern.

## 5. Edge Diagnostics

A 16-pixel-wide boundary region was compared with the tile interior.

| Statistic | Edge | Interior |
|---|---:|---:|
| Mean probability | 0.15263 | 0.09815 |
| Maximum probability | 0.50810 | 0.11143 |

These statistics include ignored pixels and are descriptive only.

The edge region has consistently higher predicted probabilities.

## 6. Constant-Input Probe

The frozen model was evaluated on two synthetic inputs:

- Four-band 256 x 256 tensor filled with 0.0
- Four-band 256 x 256 tensor filled with 0.1

Both inputs produced positive predictions at all four corners:

(0, 0), (0, 255), (255, 0), (255, 255)

| Input | Maximum probability | Edge mean | Interior mean |
|---|---:|---:|---:|
| Zeros | 0.51674 | 0.22959 | 0.17906 |
| Constant 0.1 | 0.51133 | 0.18966 | 0.13588 |

The probe strengthens the evidence for systematic boundary-sensitive
behavior that does not require real spatial image texture.

It does not establish the exact mechanism.

Potential explanations include padding effects and learned
boundary responses. These hypotheses remain unverified.

Synthetic inputs were used for diagnosis, not performance evaluation.

## 7. Root-Cause Assessment

Confirmed observations:

1. Sparse valid supervision.
2. Strong class-distribution differences across splits.
3. Weak separation between positive and negative probabilities.
4. Repeated corner predictions and elevated edge probabilities.
5. Failure to detect positive landslide pixels at threshold 0.5.

Unverified hypotheses:

1. Insufficient or unrepresentative training supervision.
2. Effects of spatial sampling and limited independent groups.
3. Boundary artifacts related to architecture or learned weights.
4. Training limitations arising from the small labeled dataset.

The current evidence cannot rank these hypotheses causally.

## 8. Loop 2 Recommendations

Priority A — Reference data

Expand verified positive and negative reference polygons, preferably
across additional independent spatial regions.

Preserve the distinction between verified negatives and unlabeled areas.

Priority B — Dataset design

Build a new versioned release using the existing curation pipeline.

Ensure that validation contains both classes and design an appropriate
independent evaluation split.

Priority C — Model investigation

Reuse the training and evaluation pipelines.

Investigate boundary behavior and training limitations through
controlled experiments, without treating the original frozen test
as an untouched model-selection resource.

Priority D — Platform integration

Prepare the dataset and model outputs for eventual integration with
GeoAI Platform, including traceable predictions and human review.

## 9. Evaluation Integrity

The L1-14 test report was finalized before this diagnostic phase.

L1-15 reuses the test samples for post-hoc error analysis only.

Its findings may guide future research questions, but the same test
data must not be presented as a fresh independent evaluation of
models developed in response to these findings.

A suitable independent evaluation design is required for future
claims of improved generalization.

## 10. Evidence and Artifacts

Scripts:

- scripts/analyze_label_coverage.py
- scripts/analyze_prediction_errors.py

Local diagnostic reports:

- artifacts/diagnostics/padena_l1_15_label_audit.json
- artifacts/diagnostics/padena_l1_15_prediction_audit.json
- artifacts/diagnostics/padena_l1_15_prediction_audit_positions.json

Frozen evaluation:

- artifacts/evaluations/padena_model_v1.0.0_test_v1.json

Frozen evaluation report SHA-256:

445d9158e86a64ae725ca5350bf79dcf427134a93264a4fccbba020ad418ab10

## 11. Research Implications

The most relevant future research questions concern incomplete
reference inventories, spatially independent evaluation, and
boundary-sensitive model behavior.

The present dataset is insufficient to establish a new
generalizable landslide detection method.

Further reference-data expansion and controlled comparison studies
are necessary before making stronger scientific claims.

## Conclusion

The baseline evaluation workflow is functional and reproducible.

The model itself does not provide useful positive-class detection
at the predefined threshold.

L1-15 identified measurable data limitations and systematic model
behaviors without modifying the frozen baseline.

These findings provide a documented basis for the Loop 2 decision.