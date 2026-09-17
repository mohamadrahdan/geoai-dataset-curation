# Loop 1 Increment 17 — Real Sampling and Image-Mask Pair Evidence

## Objective

This evidence record documents the deterministic selection, source-specific negative provenance, physical image-mask pair generation, persistence, and verification completed during L1-8.

The increment converts the complete candidate tile catalog into a concrete supervised pair population while preserving:

```text
UNLABELED != NEGATIVE
```

## Real Inputs

### Image Artifact

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

Observed image properties:

```text
bands: 4
dtype: float64 for every band
```

### Label Artifact

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

Approved label values:

```text
positive: 1
verified negative: 0
ignore or unlabeled: 255
```

### Candidate Catalog

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

Candidate catalog identity:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

### Shared Grid

```text
CRS: EPSG:32639
width: 5712 pixels
height: 5493 pixels
pixel size: 10 × 10 metres
```

Grid identity:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

## Complete Candidate Population

The real candidate catalog contains:

```text
total candidates: 870
positive candidates: 19
negative-only candidates: 31
all-ignore candidates: 820
```

Consistency check:

```text
19 + 31 + 820 = 870
```

## Source-Specific Negative Evidence

Real private reference-source counts:

```text
ordinary-negative features: 54
hard-negative features: 49
```

Source-specific raster counts:

```text
ordinary-negative pixels: 23,640
hard-negative pixels: 40,751
shared negative pixels: 3
unique union negative pixels: 64,388
```

The source-mask union was compared with every label-raster pixel having value zero.

Observed result:

```text
exact union-to-label match: true
```

This demonstrates that every negative label pixel is explained by approved ordinary-negative or hard-negative reference evidence.

## Complete Provenance Catalog

Generated artifact:

```text
artifacts/live/loop1/komeh_tile_negative_provenance_v1.catalog.json
```

Semantic identity:

```text
sha256:1cd474b5a004e0ac3f6cc0e7fd8649ae4eee5acd3e6e651491eeec90163263d1
```

Measured artifact size:

```text
256,034 bytes
```

Coverage:

```text
candidate tiles: 870
provenance records: 870
```

Complete provenance distribution:

```text
none: 826
ordinary_negative: 10
hard_negative: 21
mixed_negative: 13
```

## Deterministic Sampling Selection

Approved Loop 1 sampling behaviour:

```text
select every supervised candidate
exclude every all-ignore candidate
preserve candidate catalog order
require hard-negative source provenance
```

Generated artifact:

```text
artifacts/live/loop1/komeh_sampling_selection_v1.catalog.json
```

Selection identity:

```text
sha256:3b455b9e8616322378c44e0e373381b11b3c95db3dd80426ff243e095ed9ec6b
```

Measured artifact size:

```text
113,445 bytes
```

Selection result:

```text
selected candidates: 50
positive candidates: 19
negative-only candidates: 31
excluded all-ignore candidates: 820
```

Consistency checks:

```text
19 + 31 = 50 selected candidates
50 + 820 = 870 complete candidates
```

No random sampling or class balancing was applied.

## Selected-Tile Provenance

The 50 selected candidates contain:

```text
none: 6
ordinary_negative: 10
hard_negative: 21
mixed_negative: 13
```

Consistency check:

```text
6 + 10 + 21 + 13 = 50
```

Tile-level negative observations:

```text
source-derived tile observations: 116,695
candidate-catalog tile observations: 116,695
```

The observation count exceeds the 64,388 unique negative raster pixels because overlapping candidate windows observe some raster locations more than once.

The exact equality between provenance and candidate observations confirms complete tile-level reconciliation.

## Physical Image-Mask Pairs

Pair artifact root:

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1
```

Pair catalog:

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.catalog.json
```

Pair catalog identity:

```text
sha256:7a1a0996917a58ec071dde6fc5982c89dd605f5996b02749b8af39d676724b4b
```

Measured pair outputs:

```text
generated pairs: 50
positive pairs: 19
negative-only pairs: 31
all-ignore pairs: 0
```

Physical image-tile properties:

```text
bands: 4
dtype: float64 for every band
```

Physical mask-tile properties:

```text
bands: 1
dtype: uint8
nodata: 255
allowed values: 0, 1, 255
```

Measured artifact sizes:

```text
pair catalog: 30,319 bytes
image tiles: 26,254,212 bytes
mask tiles: 276,624 bytes
```

## Physical Pair Verification

All 50 generated pairs were verified against their selected candidate records and the approved source rasters.

Verification covered:

```text
artifact existence and readability
image and mask dimensions
image band count and dtypes
mask band count, dtype, nodata, and values
CRS equality
affine-transform equality
exact image-window pixel content
exact mask-window pixel content
positive pixel count
negative pixel count
ignore pixel count
label class
```

Observed result:

```text
expected pairs: 50
verified pairs: 50
verification errors: 0
```

## Persisted Catalog Verification

The provenance, selection, and pair catalogs were serialized as canonical JSON and compared with their expected in-memory representations.

Observed results:

```text
provenance artifact verification: PASS
selection artifact verification: PASS
pair catalog artifact verification: PASS
```

## Reproduction Command

```powershell
python -B scripts/check_real_tile_negative_provenance.py
```

Final real execution result:

```text
PASS: Real sampling artifacts and physical image-mask pairs were built and verified.
```

## Automated Verification

Focused and complete automated tests were executed throughout L1-8.

Final complete-suite command:

```powershell
python -m pytest -q
```

Final result:

```text
500 passed
```

Whitespace verification:

```powershell
git diff --check
```

Observed result:

```text
no errors
```

## Decision Records

L1-8 is governed by:

- [DR-0015: Select All Supervised Candidates Deterministically in Loop 1](../decisions/DR-0015-select-all-supervised-candidates-deterministically.md)
- [DR-0016: Preserve Negative-Source Provenance Through Sampling](../decisions/DR-0016-preserve-negative-source-provenance-through-sampling.md)
- [DR-0017: Materialize and Verify Image-Mask Pairs Before Dataset Splitting](../decisions/DR-0017-materialize-and-verify-image-mask-pairs.md)

## Limitations and Deferred Responsibilities

This increment intentionally does not establish:

- physical quality-control acceptance beyond pair correctness
- spatial train-validation-test assignments
- the final dataset manifest or version
- training-package structure
- model architecture or optimization
- baseline-model performance
- error-analysis conclusions

The current population is derived from one study area and one 2024 Sentinel-2 median composite.

Private reference data do not currently provide complete event timestamps. The current task therefore establishes spatial inventory supervision and does not claim event-date detection.

## Closure Evidence

```text
Code works: PASS
Tests pass: PASS
Required artifacts exist: PASS
Artifacts are identity-linked: PASS
Persisted catalogs are verified: PASS
Physical pairs are verified: PASS
Important decisions are documented: PASS
Evidence is measurable: PASS
```
