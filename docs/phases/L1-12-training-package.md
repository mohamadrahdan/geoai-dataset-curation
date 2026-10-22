# Phase L1-12 — Training Package

## Status

Completed — 2026-10-11

## Objective

Provide a minimal, framework-independent training-data interface
that consumes the immutable dataset release directly.

## Input

Dataset release: `padena_dataset_v1.0.0`

The release contains 50 verified image-mask pairs and the approved
spatial train/validation/test split.

## Implementation

Added:

- `src/geoai_dataset_curation/training_package.py`
- `tests/test_training_package.py`
- `scripts/check_training_package.py`

The `ReleasedSplit` reader:

- Loads the release manifest and the requested split catalog.
- Resolves image and mask paths relative to the release root.
- Preserves pair and tile identities.
- Checks image-mask alignment and label semantics.
- Reads raster samples lazily.
- Does not copy or regenerate the dataset.

## Input Contract

Image:
- Four channels in B2, B3, B4, B8 order.
- CHW layout.
- Float32 output.
- Fixed scaling: image / 10000.0.
- No clipping.

Mask:
- 0 = verified negative.
- 1 = positive.
- 255 = ignore/unlabeled.
- Original values are preserved.

A separate boolean `valid_mask` identifies supervised pixels.

This preprocessing contract must be preserved when the model is
later integrated into GeoAI Platform.

## Real Verification

Dataset release validation:
- 106 tracked files verified.
- 3 spatial groups preserved.
- 50 image-mask pairs.

Training split:
- 33 pairs.
- 8 positive pairs.
- 111893 supervised pixels.

Validation split:
- 4 pairs.
- 0 positive pairs.
- 12264 supervised pixels.

Total physically loaded:
- 37 image-mask pairs.
- 124157 supervised pixels.

The frozen test split was not read during the training-package
smoke check.

## Automated Tests

- 7 training-package tests passed.
- Full repository suite: 637 passed.

## Boundaries and Limitations

- No model training is performed in this phase.
- No model architecture is selected.
- No evaluation metrics are computed.
- Test data remain reserved for the official evaluation phase.
- The validation split contains no positive samples.
- The selected input scaling is fixed and must remain traceable.
- Dataset integrity validation remains the responsibility of
  the existing release validator.

## Completion

- [x] Code works.
- [x] Automated tests pass.
- [x] Real dataset loading succeeds.
- [x] Input and label contracts are documented.
- [x] Evidence is measurable.
- [x] No unnecessary dataset duplication.

## Next Phase

L1-13 — Baseline Model Training

The next phase will consume this training interface to train
and save `padena_model_v1.0.0`.