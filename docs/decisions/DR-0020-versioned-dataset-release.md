# DR-0020 — Versioned Dataset Release Contract

## Status

Accepted — 2026-10-10

## Context

Loop 1 has produced 50 quality-controlled image-mask pairs and an approved spatial train/validation/test split.

The baseline model requires a stable dataset interface that does not depend on temporary processing directories or manually selected image files.

Future dataset iterations must also be usable without rewriting the core training and evaluation logic.

## Decision

Create an immutable, versioned dataset release with a minimal manifest-based interface.

The first release is:

`padena_dataset_v1.0.0`

The release contains physical image and mask files, split catalogs, and relevant quality-control and spatial-split evidence.

All paths referenced by split catalogs are relative to the release directory.

The manifest provides the dataset version, source identity, split locations, file checksums, label-value contract, and documented limitations.

## Consumer Contract

Training and evaluation components should receive a dataset release path through configuration.

They must read the manifest and the requested split catalog rather than relying on hardcoded source-file locations.

A compatible future dataset version should be selectable through configuration without modifying the core training or evaluation code.

This is an architectural requirement for the upcoming model development phase, not a claim that the model loader has already been implemented.

## Label Contract

- `0`: verified negative
- `1`: positive
- `255`: ignore / unlabeled

Unlabeled pixels must never be silently converted into verified negatives.

## Split and Evaluation Policy

The approved Loop 1 split is:

- Train: 33 pairs
- Validation: 4 pairs
- Test: 13 pairs

The validation set contains no positive samples. Therefore, it must not be used to select models based on positive-class detection performance.

Baseline training settings should be predetermined.

The test split must not influence model selection or hyperparameter tuning.

Future training-data expansion must not contaminate the frozen evaluation reference. Changes to the evaluation benchmark must be explicitly versioned and reported.

## Immutability and Traceability

An existing dataset release must not be silently overwritten.

The release stores SHA-256 checksums for its tracked files and retains source catalog identities.

The dataset release files remain outside the Git source history. Source code and documentation are version-controlled separately.

Release artifact preservation must be handled explicitly; a Git commit containing the builder alone does not preserve the dataset bytes.

## Validation Boundary

The release validator checks file integrity, catalog consistency, split assignments, and portability.

It does not independently establish semantic label correctness, full geographic generalization, or complete end-to-end build reproducibility.

## Consequences

The baseline model will consume a stable versioned dataset rather than upstream curation artifacts directly.

Future compatible dataset versions can use the same consumer interface.

The first release remains scientifically limited by the number and distribution of independent spatial groups.

## Loop 2 Direction

Expand verified reference data, especially geographically independent positive examples, while preserving evaluation integrity.

The effect of improved training data should be measured against an appropriate unchanged evaluation reference.

## Final Principle

Keep the dataset release contract small, reproducible, traceable, and independent of the model implementation.