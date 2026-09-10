# Loop 1 Increment 16 — Real Candidate Tile Catalog Evidence

## Objective

This evidence record documents the construction, persistence, and verification of the real Loop 1 candidate tile catalog.

The catalog records the complete deterministic tile population before:

- sample selection
- class balancing
- hard-negative prioritization
- physical image-label pair generation
- spatial split assignment

## Real Inputs

### Image Artifact

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

### Label Artifact

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

### Shared Raster Grid

```text
CRS: EPSG:32639
width: 5712 pixels
height: 5493 pixels
pixel size: 10 × 10 metres
```

Approved grid identity:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

The real execution verified that the image and label artifacts have identical:

```text
CRS
width
height
affine transform
```

## Approved Tiling Policy

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 64 pixels
overlap percentage: 25%
edge policy: SHIFT_TO_FIT
```

Layout identity:

```text
sha256:5c4baabc2477f27ee08f921b681e8ea56a5eef3b45cdd2d3bcb98cb76637f602
```

## Generated Artifact

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

Schema version:

```text
tile-catalog-v1
```

Output name:

```text
komeh_candidate_tiles_v1
```

Measured artifact size:

```text
815,877 bytes
```

## Semantic Catalog Identity

The catalog identity is derived from canonical semantic content.

Real catalog identity:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

The identity includes:

- schema version
- source artifact paths
- grid identity
- layout identity
- deterministic record ordering
- tile identities
- pixel windows
- spatial bounds
- per-tile label counts

## Physical Artifact Identity

Physical file SHA-256:

```text
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6
```

Two consecutive executions produced:

```text
first file SHA-256:
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6

second file SHA-256:
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6

hashes equal:
True
```

This confirms deterministic physical serialization for the same inputs and implementation.

## Candidate Population

Measured catalog totals:

```text
total candidate tiles: 870
supervised tiles: 50
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
```

Consistency check:

```text
19 positive
+
31 negative-only
+
820 all-ignore
=
870 total candidates
```

## Candidate Meaning

### Positive

A candidate is positive when:

```text
positive_pixel_count > 0
```

Measured count:

```text
19
```

### Negative Only

A candidate is negative-only when:

```text
positive_pixel_count = 0
negative_pixel_count > 0
```

Measured count:

```text
31
```

This classification describes the numeric raster target only.

It does not distinguish ordinary-negative provenance from hard-negative provenance.

### All Ignore

A candidate is all-ignore when:

```text
positive_pixel_count = 0
negative_pixel_count = 0
```

Measured count:

```text
820
```

These candidates remain explicitly distinct from negative-only candidates.

The catalog therefore preserves:

```text
UNLABELED != NEGATIVE
```

## Record-Level Evidence

Every candidate record contains:

```text
stable tile identity
shared grid identity
selected layout identity
row and column indices
pixel offsets
read dimensions
output dimensions
spatial bounds
positive pixel count
negative pixel count
ignore pixel count
derived label class
supervised pixel count
padding pixel count
```

The selected edge policy produced:

```text
870 full-size records
0 partial output records
0 padded records
```

## Deterministic Ordering

The records use:

```text
row-major ordering
```

Validation confirms:

```text
unique tile identities: PASS
unique row-column positions: PASS
record grid identity consistency: PASS
record layout identity consistency: PASS
row-major ordering: PASS
```

## Artifact Verification

The persisted file was compared with the expected in-memory catalog.

Verified:

```text
artifact exists: PASS
UTF-8 decoding: PASS
JSON decoding: PASS
schema version: PASS
catalog identity: PASS
tile count: PASS
record ordering: PASS
record content: PASS
complete artifact comparison: PASS
```

Execution result:

```text
PASS: Real candidate tile catalog was written and verified.
```

## Reproduction Command

```powershell
python scripts/build_real_tile_catalog.py
```

Physical determinism check:

```powershell
$firstHash = (Get-FileHash artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json -Algorithm SHA256).Hash

python scripts/build_real_tile_catalog.py

$secondHash = (Get-FileHash artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json -Algorithm SHA256).Hash

$firstHash -eq $secondHash
```

Observed result:

```text
True
```

## Automated Validation

Focused catalog tests:

```text
19 passed
```

Complete test suite:

```text
394 passed
```

Whitespace validation:

```text
git diff --check: clean
```

The automated tests cover:

- catalog contracts
- label-derived classes
- pixel-count consistency
- identity validation
- row-major ordering
- duplicate detection
- deterministic catalog construction
- spatial-bound construction
- padding accounting
- stable catalog identity
- canonical serialization
- physical writing
- persisted artifact verification
- modified artifact detection

## Repository and Artifact Boundary

The repository records:

```text
catalog contracts
catalog validation
catalog generation
catalog identity
canonical serialization
artifact verification
real execution script
automated tests
evidence documentation
```

The generated live artifact remains under:

```text
artifacts/live/loop1/
```

It is not committed to version control under the existing artifact policy.

## Downstream Boundary

The catalog is the complete candidate population.

It is not the final dataset.

The next flow is:

```text
verified candidate catalog
+
positive source provenance
+
ordinary-negative source provenance
+
hard-negative source provenance
+
sampling policy
↓
selected candidate records
↓
physical image-label tile pairs
```

The following decisions remain outside this increment:

- sampling ratios
- all-ignore exclusion or retention
- hard-negative prioritization
- final pair count
- spatial split assignment
- dataset version publication

## Measurable Evidence Summary

```text
real image-label alignment: PASS
approved grid identity: PASS
approved layout identity: PASS
candidate records: 870
positive candidates: 19
negative-only candidates: 31
all-ignore candidates: 820
semantic catalog identity: stable
physical file identity: stable
physical rerun equality: True
artifact verification: PASS
focused tests: 19 passed
complete tests: 394 passed
git diff --check: clean
```

## Evidence Result

```text
Code works: PASS
Tests pass: PASS
Artifact exists: PASS
Artifact is deterministic: PASS
Artifact is verified: PASS
Decision is documented: PASS
Evidence is measurable: PASS
```