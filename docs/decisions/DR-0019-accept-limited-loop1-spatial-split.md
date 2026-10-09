# DR-0019 — Accept Limited Spatial Split for Loop 1 Baseline

## Status

Accepted — 2026-10-09

## Context

The first real Komeh dataset contains 50 verified image-mask pairs distributed across three independent spatial groups.

The group structure prevents a three-way train/validation/test split in which every subset contains positive samples without breaking the selected spatial independence constraint.

## Decision

Proceed with the existing 50-pair dataset and an explicit group-level assignment:

- Train: 33 pairs, including 8 positives
- Validation: 4 pairs, including 0 positives
- Test: 13 pairs, including 11 positives

Preserve the spatial independence requirement and do not artificially redistribute overlapping samples to improve class proportions.

The training procedure must use predetermined baseline settings rather than positive-class validation optimization. The test set must remain excluded from training and model selection.

## Rationale

Loop 1 aims to demonstrate a complete, reproducible workflow from reference polygons to a versioned dataset, baseline model, evaluation, error analysis, and platform integration.

The objective is not to establish state-of-the-art performance or statistically robust geographic generalization.

## Consequences

1. The baseline model is trained on the current limited dataset.
2. The validation split cannot assess positive-class detection performance.
3. Evaluation results must explicitly disclose spatial and class-distribution limitations.
4. No claims of broad geographic generalization are permitted.
5. The frozen test set must not be used for hyperparameter tuning or incorporated into subsequent training data.

## Future Dataset Versions

Dataset identity and paths must be supplied through configuration or versioned manifests.

Training and evaluation logic must not require source-code modifications when a new compatible dataset version is introduced.

## Loop 2 Priority

Increase the quantity, diversity, and geographic independence of verified reference samples.

Evaluate the effect of the improved training data on model performance using an unchanged, independent test benchmark, while retaining the baseline results and their limitations.

## Final Principle

Complete Loop 1 with known and documented dataset limitations. Treat improved reference-data coverage as a measured scientific objective for subsequent iterations.