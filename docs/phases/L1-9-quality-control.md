# Phase L1-9 — Quality Control

## Status

Completed

## Objective

The objective of L1-9 was to evaluate the complete materialized image-mask pair population as a dataset-quality object before spatial split assignment.

The phase had to establish a pre-split acceptance gate combining:

```text
automated pair inspection
+
cross-artifact traceability
+
complete human visual review
```

## Starting Point

L1-9 began with the verified outputs of L1-8:

```text
complete candidate tiles: 870
selected supervised tiles: 50
positive pairs: 19
negative-only pairs: 31
excluded all-ignore candidates: 820
physical image-mask pairs: 50
```

The input artifacts already preserved stable links among:

- the candidate tile catalog
- the deterministic sampling selection
- the negative-source provenance catalog
- the image-mask pair catalog
- the physical image and mask tiles

## Implemented Work

### Quality-Control Contracts

Implemented explicit contracts for:

```text
finding severity
pair quality-control status
pair-level findings
pair quality-control results
image-band statistics
image-content inspection
traceability results
visual-review decisions
visual-review catalogs
pair quality-control reports
```

The supported automated result states are:

```text
pass
warning
fail
```

The supported human review states are:

```text
pending
pass
review
fail
```

### Raster-Integrity Inspection

Implemented physical inspection of every image-mask pair for:

- artifact existence and readability
- raster dimensions
- image and mask band counts
- image and mask dtypes
- mask nodata
- CRS equality
- affine-transform equality

### Mask-Semantic Inspection

Implemented verification of:

- allowed mask values
- positive, negative, and ignore pixel counts
- expected tile label class
- mask count consistency
- invalid or unsupported mask semantics

### Image-Content Inspection

Implemented image-content checks for:

- finite pixel values
- NaN and infinite values
- empty or all-zero images
- per-band minimum and maximum
- per-band mean and standard deviation
- constant bands
- constant complete images

Non-finite and all-zero image content are treated as errors.

Constant bands remain visible as warnings rather than being rejected through an arbitrary variance threshold.

### Cross-Artifact Traceability

Implemented complete verification across:

```text
candidate catalog
sampling selection
negative provenance catalog
pair catalog
physical image files
physical mask files
```

Traceability inspection detects:

- missing pairs
- unexpected image files
- unexpected mask files
- broken pair identities
- incorrect catalog links
- incomplete selected-tile coverage

### Automated Quality-Control Reports

Implemented deterministic pair-level reports containing:

- overall status
- pair-level statuses
- structured findings
- image-band statistics
- mask statistics
- traceability results
- pass, warning, fail, and finding counts

Reports are persisted as canonical JSON artifacts.

### Visual-Review Contact Sheets

Implemented deterministic PNG contact sheets showing, for every pair:

```text
image
mask
overlay
```

Contact sheets preserve catalog order and display pair metadata needed for manual review.

### Persisted Human Review

Implemented:

- review templates linked to the pair catalog
- one review decision for every pair
- canonical JSON persistence
- complete and incomplete review validation
- rejection of missing, duplicated, or unknown pair decisions
- optional enforcement that no decision remains pending

### Persisted Input Loading

Implemented loading of the persisted L1-8 artifacts without regenerating them.

The loader reconstructs and validates:

- the candidate tile catalog
- the sampling selection
- the negative provenance catalog
- the image-mask pair catalog
- every stored semantic identity

### Real Quality-Control Runtime

Implemented:

```text
scripts/check_real_pair_quality_control.py
```

The script:

1. loads and verifies the persisted L1-8 inputs
2. executes automated quality control
3. writes the structured quality-control report
4. creates deterministic visual-review contact sheets
5. creates a review template only when one does not already exist
6. preserves completed contact sheets and human decisions on repeated execution

## Real Runtime Flow

The completed L1-9 runtime flow is:

```text
persisted L1-8 catalogs
↓
identity-verified artifact loading
↓
pair raster-integrity inspection
↓
mask-semantic inspection
↓
image-content inspection
↓
cross-artifact traceability verification
↓
automated quality-control report
↓
deterministic visual-review contact sheets
↓
persisted human decisions
↓
complete pre-split acceptance gate
```

## Real Artifacts

### Automated Quality-Control Report

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.qc.json
```

Schema:

```text
pair-quality-control-report-v1
```

### Visual-Review Contact Sheets

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1_visual_review
```

### Human Review Catalog

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.visual_review.json
```

### Pair Catalog Under Review

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.catalog.json
```

Pair catalog identity:

```text
sha256:7a1a0996917a58ec071dde6fc5982c89dd605f5996b02749b8af39d676724b4b
```

## Measurable Evidence

### Automated Pair Results

```text
pair count: 50
pass count: 50
warning count: 0
fail count: 0
finding count: 0
overall status: pass
```

### Traceability Results

```text
expected pairs: 50
verified pairs: 50
discovered image files: 50
discovered mask files: 50
traceability findings: 0
traceability status: pass
```

### Human Visual Review

```text
pairs per contact sheet: 5
contact sheets: 10
reviewed pairs: 50
human pass decisions: 50
human pending decisions: 0
human review decisions: 0
human fail decisions: 0
```

The completed catalog passed validation with:

```text
require_complete: true
```

### Automated Tests

```text
555 passed
```

## Practical Verification

Real end-to-end execution:

```powershell
python scripts/check_real_pair_quality_control.py
```

Observed result:

```text
Pair count: 50
Contact sheets: 10
Visual-review template created: False
```

Complete automated suite:

```powershell
python -m pytest -q
```

Whitespace verification:

```powershell
git diff --check
```

## Decision

L1-9 established:

- [DR-0018: Require Automated and Human Quality Control Before Spatial Splitting](../decisions/DR-0018-require-automated-and-human-quality-control-before-spatial-splitting.md)

Detailed real evidence is recorded in:

- [Loop 1 Increment 18 — Real Pair Quality-Control Evidence](../evidence/loop1_increment_18_real_pair_quality_control.md)

## Acceptance Result

The real 50-pair population passed both automated and human quality control.

It is accepted as the complete pre-split supervised population for the next phase.

This acceptance means that the pairs are:

- physically readable
- spatially aligned
- semantically valid under the label contract
- linked to their selected candidates and provenance
- complete on disk
- free from detected automated findings
- visually reviewed and accepted

## Scientific Meaning

Quality-control acceptance establishes that the current pairs are technically and semantically fit to enter spatial split design.

It does not establish that the current population is sufficient for operational generalization.

The current dataset contains only 19 positive tiles, and overlapping tiles are not fully independent observations.

Those constraints must be addressed through leakage-aware spatial splitting, baseline evaluation, error analysis, and targeted data expansion in later loops.

## Limitations

L1-9 intentionally does not:

- assign train, validation, or test subsets
- define spatial groups
- prevent split leakage through split assignment
- publish a final dataset manifest
- release `padena_dataset_v1.0.0`
- create a training package
- train or evaluate a model
- convert all-ignore candidates into negative supervision

The 820 all-ignore candidates remain an unlabeled pool rather than accepted negative training samples.

## Completion Checklist

- [x] Code and real workflow work
- [x] Automated tests pass
- [x] Persisted inputs are identity-verified
- [x] Automated quality-control report exists
- [x] All physical pairs pass automated inspection
- [x] Cross-artifact traceability passes
- [x] Visual-review contact sheets exist
- [x] Every pair has a completed human decision
- [x] Repeated execution preserves completed review artifacts
- [x] Important decision is documented
- [x] Evidence is measurable

## Next Phase

The next phase is:

```text
L1-10 — Spatial Split
```

L1-10 must assign the accepted pair population to train, validation, and test subsets while preventing spatial leakage from overlapping or neighboring tiles.

The following responsibilities remain deferred:

```text
L1-11 — Manifest and Dataset Version
L1-12 — Training Package
```
