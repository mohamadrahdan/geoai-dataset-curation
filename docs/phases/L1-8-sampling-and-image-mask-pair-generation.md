# Phase L1-8 â€” Sampling and Image-Mask Pair Generation

## Status

Completed

## Objective

The objective of L1-8 was to convert the complete deterministic candidate tile catalog into an auditable supervised selection and a verified physical image-mask pair population.

The phase had to preserve the distinction between:

```text
verified negative supervision
```

and:

```text
unlabeled or ignored raster space
```

It also had to preserve ordinary-negative and hard-negative source provenance after both sources were encoded as label value zero.

## Starting Point

L1-8 began with:

```text
a real aligned four-band Sentinel-2 image
a real uint8 label raster
an exact shared raster grid
an approved deterministic tiling policy
a complete 870-record candidate tile catalog
stable grid, layout, tile, and catalog identities
private ordinary-negative and hard-negative reference sources
```

Candidate population:

```text
positive candidates: 19
negative-only candidates: 31
all-ignore candidates: 820
total candidates: 870
```

## Implemented Work

### Sampling Contracts and Eligibility Rules

Implemented explicit contracts for:

```text
sampling policy
sampling eligibility
sampling selection
negative provenance
image-mask pairs
```

Eligibility preserves:

```text
supervised pixels present -> eligible
all pixels ignored -> ineligible
```

### Provenance-Aware Sampling Policy

Implemented separate ordinary-negative and hard-negative masks on the approved grid.

For every candidate tile, provenance records preserve:

- ordinary-negative pixel count
- hard-negative pixel count
- shared pixel count
- unique union count
- provenance kind

The source-specific mask union exactly matches every label-raster pixel having value zero.

### Deterministic Selection and Selection Catalog

Implemented a Loop 1 policy that:

```text
selects all supervised candidates
excludes all-ignore candidates
preserves candidate catalog order
requires source provenance for hard negatives
```

The selection has stable identity, validation, canonical persistence, and persisted artifact verification.

### Negative Provenance Catalog

Implemented:

```text
complete 870-record provenance generation
record and catalog validation
stable semantic identity
canonical JSON persistence
persisted artifact verification
```

### Image-Mask Pair Contracts and Identity

Implemented pair and pair-catalog contracts linking every physical pair to:

- one selected tile
- the candidate catalog
- the sampling selection
- the negative provenance catalog
- the source image and label artifacts

### Physical Pair Generation

Implemented deterministic source-window extraction and GeoTIFF materialization.

The generator creates:

```text
one four-band image tile
+
one single-band uint8 mask tile
```

for every selected candidate.

### Pair Persistence and Verification

Implemented:

```text
pair-catalog canonical serialization
pair-catalog artifact verification
physical image-mask artifact verification
exact source-window pixel comparison
spatial metadata comparison
mask-value and label-count reconciliation
```

## Real Runtime Flow

The completed L1-8 runtime flow is:

```text
complete candidate tile catalog
â†“
sampling eligibility assessment
â†“
source-specific negative masks
â†“
complete tile provenance catalog
â†“
deterministic supervised selection
â†“
persisted selection catalog
â†“
physical image and mask extraction
â†“
stable pair identities
â†“
complete pair catalog
â†“
physical and catalog verification
```

## Real Artifacts

### Provenance Catalog

```text
artifacts/live/loop1/komeh_tile_negative_provenance_v1.catalog.json
```

Identity:

```text
sha256:1cd474b5a004e0ac3f6cc0e7fd8649ae4eee5acd3e6e651491eeec90163263d1
```

### Sampling Selection Catalog

```text
artifacts/live/loop1/komeh_sampling_selection_v1.catalog.json
```

Identity:

```text
sha256:3b455b9e8616322378c44e0e373381b11b3c95db3dd80426ff243e095ed9ec6b
```

### Pair Catalog

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1.catalog.json
```

Identity:

```text
sha256:7a1a0996917a58ec071dde6fc5982c89dd605f5996b02749b8af39d676724b4b
```

### Physical Pair Root

```text
artifacts/live/loop1/komeh_image_mask_pairs_v1
```

## Measurable Evidence

### Source Evidence

```text
ordinary-negative features: 54
hard-negative features: 49
ordinary-negative pixels: 23,640
hard-negative pixels: 40,751
shared negative pixels: 3
unique union negative pixels: 64,388
exact union-to-label match: true
```

### Selection Evidence

```text
complete candidates: 870
selected candidates: 50
selected positive candidates: 19
selected negative-only candidates: 31
excluded all-ignore candidates: 820
```

### Selected Provenance Evidence

```text
none: 6
ordinary_negative: 10
hard_negative: 21
mixed_negative: 13
```

### Pair Evidence

```text
generated pairs: 50
verified pairs: 50
positive pairs: 19
negative-only pairs: 31
verification errors: 0
```

### Artifact Sizes

```text
provenance catalog: 256,034 bytes
selection catalog: 113,445 bytes
pair catalog: 30,319 bytes
image tiles: 26,254,212 bytes
mask tiles: 276,624 bytes
```

### Automated Tests

```text
500 passed
```

## Practical Verification

Real end-to-end execution:

```powershell
python -B scripts/check_real_tile_negative_provenance.py
```

Observed result:

```text
PASS: Real sampling artifacts and physical image-mask pairs were built and verified.
```

Complete automated suite:

```powershell
python -m pytest -q
```

Whitespace verification:

```powershell
git diff --check
```

## Decisions

L1-8 established:

- [DR-0015: Select All Supervised Candidates Deterministically in Loop 1](../decisions/DR-0015-select-all-supervised-candidates-deterministically.md)
- [DR-0016: Preserve Negative-Source Provenance Through Sampling](../decisions/DR-0016-preserve-negative-source-provenance-through-sampling.md)
- [DR-0017: Materialize and Verify Image-Mask Pairs Before Dataset Splitting](../decisions/DR-0017-materialize-and-verify-image-mask-pairs.md)

Detailed real evidence is recorded in:

- [Loop 1 Increment 17 â€” Real Sampling and Image-Mask Pair Evidence](../evidence/loop1_increment_17_real_sampling_and_image_mask_pairs.md)

## Scientific Meaning

The selected 50 pairs are the complete supervised population produced by the approved Loop 1 image, label, grid, tiling, and sampling policies.

They are sufficient to establish the first real baseline-training cycle, but they are not assumed to be sufficient for a final operational or spatially generalizable model.

Later training, evaluation, and error analysis must test whether the dominant limitation is associated with:

- sample count
- class imbalance
- spatial diversity
- reference-label quality
- four-band Sentinel-2 information
- model or optimization choices

L1-8 does not decide the answer in advance.

## Limitations

L1-8 intentionally does not:

- perform final physical quality-control acceptance
- assign train, validation, or test subsets
- publish a final dataset manifest
- create the versioned dataset release
- create a training package
- train or evaluate a model
- infer event dates for reference polygons

The current artifacts represent one study area and one 2024 Sentinel-2 median composite.

## Completion Checklist

- [x] Code or workflow works
- [x] Tests and practical checks pass
- [x] Required artifacts exist
- [x] Stable identities are recorded
- [x] Persisted catalogs are verified
- [x] Physical pairs are verified
- [x] Important decisions are documented
- [x] Evidence is measurable

## Next Phase

The next phase is:

```text
L1-9 â€” Quality Control
```

L1-9 will evaluate the selected and materialized pair population as a dataset-quality object before spatial split assignment.

The following responsibilities remain deferred:

```text
L1-10 â€” Spatial Split
L1-11 â€” Manifest and Dataset Version
L1-12 â€” Training Package
```