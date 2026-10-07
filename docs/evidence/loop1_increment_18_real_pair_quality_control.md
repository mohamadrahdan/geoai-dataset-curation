# Loop 1 Increment 18 — Real Pair Quality-Control Evidence

## Objective

This evidence record documents the automated and human quality control completed for the real Loop 1 image-mask pair population before spatial split assignment.

The increment evaluates the 50 physical pairs produced in L1-8 as a complete dataset-quality object.

The acceptance boundary requires:

```text
automated raster and semantic inspection
+
complete cross-artifact traceability
+
human visual review of every pair
```

## Real Inputs

### Candidate Tile Catalog

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

Identity:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

### Sampling Selection

```text
artifacts/live/loop1/komeh_sampling_selection_v1.catalog.json
```

Identity:

```text
sha256:3b455b9e8616322378c44e0e373381b11b3c95db3dd80426ff243e095ed9ec6b
```

### Negative Provenance Catalog

```text
artifacts/live/loop1/komeh_tile_negative_provenance_v1.catalog.json
```

Identity:

```text
sha256:1cd474b5a004e0ac3f6cc0e7fd8649ae4eee5acd3e6e651491eeec90163263d1
```

### Image-Mask Pair Catalog

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.catalog.json
```

Identity:

```text
sha256:7a1a0996917a58ec071dde6fc5982c89dd605f5996b02749b8af39d676724b4b
```

The persisted input artifacts were loaded rather than regenerated.

Every stored identity was checked against the reconstructed semantic content before quality control began.

## Quality-Control Population

The inspected population contains:

```text
total pairs: 50
positive pairs: 19
negative-only pairs: 31
```

Expected image properties:

```text
width: 256 pixels
height: 256 pixels
bands: 4
dtype: float64
```

Expected mask properties:

```text
width: 256 pixels
height: 256 pixels
bands: 1
dtype: uint8
nodata: 255
allowed values: 0, 1, 255
```

## Automated Inspection

The automated inspection evaluated every pair for:

```text
raster existence and readability
image and mask dimensions
image band count and dtype
mask band count, dtype, and nodata
allowed mask values
positive, negative, and ignore counts
label-class consistency
CRS equality
affine-transform equality
non-finite image values
empty or all-zero image content
constant image bands
pair identity
cross-artifact traceability
missing physical artifacts
unexpected physical artifacts
```

Generated report:

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.qc.json
```

Report schema:

```text
pair-quality-control-report-v1
```

Overall automated result:

```text
status: pass
pair count: 50
pass count: 50
warning count: 0
fail count: 0
finding count: 0
```

Every inspected pair passed without warnings or errors.

## Cross-Artifact Traceability

Traceability verification connected the candidate catalog, sampling selection, negative provenance catalog, pair catalog, and physical pair files.

Observed result:

```text
traceability status: pass
expected pair count: 50
verified pair count: 50
discovered image file count: 50
discovered mask file count: 50
traceability findings: 0
```

No missing, unexpected, duplicated, or unlinked image or mask artifact was detected.

## Human Visual Review

Visual-review contact sheets were generated at:

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1_visual_review
```

The review layout contains three views for every pair:

```text
image tile
colorized mask
mask overlay on image
```

Review batching:

```text
pairs per contact sheet: 5
contact sheets: 10
reviewed pairs: 50
```

The review checked for:

- corrupted or empty visual content
- image-mask displacement
- rotation or orientation errors
- implausible mask placement
- unexpected edge or padding artifacts
- visually inconsistent image-mask overlays

Persisted review catalog:

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.visual_review.json
```

Reviewer:

```text
Mohammad Rahdan
```

Completed review result:

```text
human pass decisions: 50
human pending decisions: 0
human review decisions: 0
human fail decisions: 0
```

The completed review catalog was validated with:

```text
require_complete: true
```

## Repeatability and Preservation

The real quality-control script is:

```text
scripts/check_real_pair_quality_control.py
```

Repeated execution preserves:

- existing contact sheets
- completed human decisions
- the linkage to the accepted pair catalog

Observed repeated-execution result:

```text
pair count: 50
contact sheets: 10
visual-review template created: false
```

The script does not replace a completed visual-review catalog with a new pending template.

## Practical Verification

Real quality-control execution:

```powershell
python scripts/check_real_pair_quality_control.py
```

Complete automated suite:

```powershell
python -m pytest -q
```

Observed result:

```text
555 passed
```

Whitespace verification:

```powershell
git diff --check
```

Observed result:

```text
no whitespace errors
```

## Acceptance Result

The complete real pair population satisfies the L1-9 pre-split quality-control gate:

```text
automated report status = pass
traceability status = pass
automated fail count = 0
verified pair count = expected pair count
human pending count = 0
human review count = 0
human fail count = 0
human pass count = expected pair count
```

Therefore:

```text
the 50-pair population is accepted for spatial split design
```

## Scientific Interpretation

The accepted population is the complete supervised population produced from the approved Loop 1 image, labels, grid, tiling policy, and sampling policy.

Quality-control acceptance demonstrates that the pairs are technically intact, semantically consistent with their persisted contracts, traceable to their inputs, and visually aligned.

It does not demonstrate that 50 pairs are sufficient for operational generalization.

That question must be evaluated through spatial splitting, baseline training, held-out evaluation, and error analysis.

## Limitations

This increment intentionally does not:

- assign train, validation, or test subsets
- define spatial grouping or leakage prevention
- create the final dataset manifest
- release the versioned dataset
- construct a training package
- train or evaluate a segmentation model
- infer labels for the 820 all-ignore candidate tiles

The next phase must preserve spatial independence while assigning the accepted pairs to dataset subsets.

## Decision Link

The governing decision is:

- [DR-0018: Require Automated and Human Quality Control Before Spatial Splitting](../decisions/DR-0018-require-automated-and-human-quality-control-before-spatial-splitting.md)
