# DR-0018 — Require Automated and Human Quality Control Before Spatial Splitting

## Status

Accepted

## Context

L1-8 produced a deterministic and physically verified population of 50 image-mask pairs.

Physical pair verification established that every generated image and mask:

- exists and is readable
- matches the selected tile dimensions
- preserves the expected CRS and affine transform
- contains the exact source-window pixels
- preserves the expected mask values and label counts

Those checks are necessary, but they do not provide a complete dataset-quality acceptance boundary.

Before spatial split assignment, the workflow must also detect:

- unreadable or malformed raster content
- unexpected image band counts or dtypes
- non-finite or empty image values
- constant image bands
- invalid mask semantics
- missing or extra pair artifacts
- broken cross-artifact traceability
- visually apparent image-mask misalignment
- corrupted or implausible visual content

Assigning train, validation, or test subsets before this review would allow defective pairs to enter a versioned dataset split.

## Decision

Every materialized image-mask pair must pass a pre-split quality-control gate containing both automated inspection and persisted human visual review.

### Automated Quality Control

The automated gate must inspect every pair for:

- image and mask existence
- raster readability
- image and mask dimensions
- CRS and affine-transform equality
- expected image band count and dtype
- finite image values
- empty or all-zero image content
- constant image bands
- mask band count, dtype, nodata, and allowed values
- mask label counts and label class
- pair identity and cross-artifact traceability
- missing or unexpected physical image and mask files

The complete result must be persisted as a structured pair-level quality-control report.

Automated errors produce a failing result.

Automated warnings must remain visible and require an explicit review decision rather than being silently discarded.

### Human Visual Review

Every pair must be included in deterministic contact sheets showing:

- the image tile
- the colorized mask
- the mask overlaid on the image

A persisted review catalog must link every human decision to the exact pair catalog and pair identity.

Allowed review states are:

```text
pending
pass
review
fail
```

A review catalog is not complete while any pair remains pending.

A pair marked for review or failure must be resolved before the population is accepted for spatial splitting.

### Pre-Split Acceptance Gate

The pair population may proceed to spatial split assignment only when:

```text
automated report status = pass
traceability status = pass
automated fail count = 0
all expected pairs are verified
human pending count = 0
human review count = 0
human fail count = 0
human pass count = expected pair count
```

Quality control evaluates the pair population before split membership can influence inspection or acceptance decisions.

## Consequences

### Positive Consequences

- corrupted pairs are detected before dataset splitting
- automated and visual checks remain separate and auditable
- every visual decision remains linked to a stable pair identity
- missing and unexpected files cannot pass silently
- split assignment operates only on an accepted pair population
- repeated execution preserves completed human decisions and contact sheets

### Costs and Limitations

- every pair requires visual inspection
- large future datasets may require reviewer assignment and review batching
- visual acceptance does not prove label completeness outside the reviewed reference areas
- successful quality control does not prove that the dataset is large enough for operational generalization
- warnings and disputed labels may require expert adjudication

## Alternatives Considered

### Rely Only on Physical Pair Verification

Rejected because exact source-window reproduction does not detect all image-content or visual-label problems.

### Rely Only on Automated Quality Control

Rejected because some alignment, interpretation, and plausibility problems are more reliably detected visually.

### Perform Quality Control After Spatial Splitting

Rejected because defective pairs could already influence split composition and versioned dataset statistics.

### Review Only a Random Subset

Rejected for Loop 1 because the real supervised population contains only 50 pairs and complete review is practical.

## Implementation Evidence

Implemented capabilities include:

- explicit quality-control contracts and validation
- raster-integrity inspection
- mask-semantic inspection
- image-content inspection
- cross-artifact traceability verification
- deterministic visual-review contact sheets
- persisted human review decisions
- structured automated quality-control reports
- loading and identity verification of persisted L1-8 inputs
- repeatable real-artifact execution without overwriting completed reviews

Real Loop 1 results:

```text
expected pairs: 50
automated pass pairs: 50
automated warning pairs: 0
automated fail pairs: 0
automated findings: 0
verified traceability pairs: 50
discovered image files: 50
discovered mask files: 50
contact sheets: 10
human pass decisions: 50
human pending decisions: 0
human review decisions: 0
human fail decisions: 0
```

Automated test evidence:

```text
555 passed
```

## Related Artifacts

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.catalog.json
artifacts/live/loop1/komeh_image_mask_pairs_v1.qc.json
artifacts/live/loop1/komeh_image_mask_pairs_v1_visual_review
artifacts/live/loop1/komeh_image_mask_pairs_v1.visual_review.json
scripts/check_real_pair_quality_control.py
```

## Scope Boundary

This decision accepts the quality-controlled pair population for the next phase.

It does not:

- assign train, validation, or test splits
- define spatial grouping or leakage prevention
- publish the final dataset manifest
- release a versioned dataset
- construct the training package
- train or evaluate a model

Those responsibilities remain assigned to later Loop 1 phases.
