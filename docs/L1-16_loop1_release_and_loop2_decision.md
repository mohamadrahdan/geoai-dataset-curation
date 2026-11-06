# L1-16 — Loop 1 Release and Loop 2 Decision

## 1. Purpose

Close the first development loop of the GeoAI dataset-curation
project and establish a documented handoff to the existing
GeoAI Platform.

This release represents an engineering baseline, not a
production-ready landslide detection system.

## 2. Release Versions

| Component | Version |
|---|---|
| Python package | 0.1.0 |
| Repository release tag | v0.1.0 (planned) |
| Dataset | padena_dataset_v1.0.0 |
| Model | padena_model_v1.0.0 |

The dataset and model releases remain frozen.

## 3. Loop 1 Deliverables

Loop 1 established a reproducible workflow covering:

- Geospatial reference validation
- Sentinel-2 image preparation
- Exact-grid image and label alignment
- Verified-negative and ignored-label semantics
- Tiling, sampling, and image-mask pairing
- Automated and visual quality control
- Spatial leakage-aware splitting
- Immutable dataset packaging
- Framework-independent training inputs
- Baseline model training
- Frozen model evaluation
- Post-hoc error analysis

The released dataset contains:

- 50 verified four-band image-mask pairs
- 33 training tiles
- 4 validation tiles
- 13 test tiles
- 3 connected spatial groups
- 106 SHA-256-tracked release files

## 4. Baseline Evaluation

The frozen Small U-Net was trained for 10 epochs using
four Sentinel-2 bands and masked binary cross-entropy.

Independent test evaluation:

| Metric | Result |
|---|---:|
| Positive IoU | 0.000000 |
| F1 | 0.000000 |
| ROC-AUC | 0.531839 |
| Average Precision | 0.799901 |
| True positives | 0 |
| True negatives | 4125 |
| False positives | 1 |
| False negatives | 14941 |

The baseline did not demonstrate useful landslide detection
at the predefined threshold of 0.5.

Average Precision must be interpreted against the high
positive prevalence among valid test pixels.

The model is retained as an engineering baseline.

## 5. Confirmed Limitations

The following observations were established:

- Valid label coverage is sparse across all splits.
- Validation contains no positive labeled pixels.
- Positive class prevalence differs substantially
  between training and testing.
- Spatial independence is limited by three groups.
- Positive and negative probability distributions
  show weak separation.
- Repeated corner predictions occur in all test tiles.
- Constant-input probes also produce corner predictions.

The exact cause of the boundary-sensitive behavior
remains unverified.

No model retraining or threshold adjustment was performed
after the frozen test evaluation.

## 6. Loop 1 Release Decision

Decision: RELEASE AS ENGINEERING BASELINE.

The software workflow is suitable for demonstrating
reproducibility, data provenance, model lifecycle handling,
and transparent evaluation.

The current model is not suitable for operational
landslide detection.

The repository release documents the software and
its verified baseline results.

Local model weights, dataset artifacts, and diagnostic
reports are not automatically included in the Git release.

## 7. Immediate Next Step: GeoAI Platform Integration

Integrate the frozen Loop 1 model into the existing
GeoAI Platform through its plugin-based inference system.

Initial integration scope:

1. Load and verify the frozen model artifact.
2. Apply the recorded four-band preprocessing contract.
3. Run real model inference through the existing backend.
4. Display probability maps through the existing frontend.
5. Preserve model version and provenance in run metadata.

The integration must clearly identify the model as an
engineering baseline with known performance limitations.

The complete training dataset does not need to be copied
into the platform runtime.

The integration should remain reusable for future
model releases.

## 8. Loop 2 Development Decision

Decision: PROCEED WITH A NEW DATA AND MODEL ITERATION.

Priority 1: Investigate systematic boundary behavior
through controlled architecture and inference experiments.

Priority 2: Expand verified positive and negative
reference polygons across additional spatial regions.

Priority 3: Produce a new versioned dataset release
using the existing curation workflow.

Priority 4: Train and evaluate a revised model with
a stronger validation and independent test design.

Priority 5: Register the new model release in the same
GeoAI Platform integration.

The original test data have been used for post-hoc
diagnostics and must not be presented as untouched
independent evidence for future models developed in
response to these findings.

## 9. Future Release Cycle

The planned development pattern is:

Loop completion
→ Dataset and model release
→ Platform model registration
→ Integration verification
→ Next development loop

This process allows the platform to evolve without
rebuilding its inference integration for each model version.

## 10. Final Verification

- Repository tests: 664 passed
- Working tree before release work: clean
- Dataset release validation: passed (106 files verified)
- Dataset relocation validation: passed
- Training package smoke check: passed (37 train/validation pairs)
- Frozen test data: not accessed during final smoke checks
- GitHub CI: pending
- Repository release: pending

The final release must be tagged on the merged main branch.

## Conclusion

Loop 1 established a traceable, tested, end-to-end
GeoAI dataset and baseline-model workflow.

The model's predictive limitations are explicitly
documented rather than hidden.

The next engineering milestone is integration with
the existing GeoAI Platform, followed by a new data
and model improvement cycle.