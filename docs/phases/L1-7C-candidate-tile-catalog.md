# L1-7C — Candidate Tile Catalog and Tiling Closure

## Objective

The objective of L1-7C was to convert the approved Loop 1 tiling policy into a complete, persistent, deterministic, and verifiable candidate tile catalog.

This increment closes the boundary between:

```text
deterministic tiling
```

and:

```text
sampling and pair generation
```

L1-7C does not select training samples or create physical image-label tile pairs.

## Starting Point

L1-7C began with:

```text
a real aligned Sentinel-2 image
a real label raster
an exact shared raster grid
validated tiling contracts
stable tile-window identities
deterministic window generation
an evidence-based Loop 1 tiling policy
```

Approved layout:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 25%
edge policy: SHIFT_TO_FIT
```

## Completed Increments

### L1-7C.1 — Candidate Tile Catalog Contract

Introduced:

```text
TileCandidateRecord
TileCatalog
TileLabelClass
TILE_CATALOG_SCHEMA_VERSION
```

Each candidate record stores:

- stable tile identity
- grid identity
- layout identity
- row and column position
- source pixel offsets
- read dimensions
- output dimensions
- geographic bounds
- positive pixel count
- negative pixel count
- ignore pixel count
- derived supervision count
- derived label class
- padding count

The complete catalog stores:

- schema version
- output identity
- source image path
- source label path
- grid identity
- layout identity
- ordered candidate records

### L1-7C.2 — Catalog Validation

Implemented validation for:

```text
schema version
required identity fields
SHA-256 identity format
non-negative indices and offsets
positive dimensions
read-output dimension consistency
non-negative label counts
complete output-pixel accounting
finite spatial bounds
valid bound ordering
grid identity consistency
layout identity consistency
unique tile identities
unique row-column positions
deterministic row-major ordering
non-empty candidate population
```

The catalog rejects inconsistent or ambiguous records before persistence.

### L1-7C.3 — Deterministic Catalog Generation

Implemented deterministic conversion from:

```text
aligned label array
+
validated tiling request
+
generated tile windows
```

into:

```text
validated candidate tile catalog
```

For each tile window, generation computes:

- real source-label slice
- positive pixel count
- negative pixel count
- source ignore pixel count
- padded ignore pixel count
- geographic bounds
- label-derived candidate class

Repeated generation from the same input produces an equal in-memory catalog.

### L1-7C.4 — Stable Catalog Identity

Introduced a semantic catalog identity based on canonical content.

The identity includes:

```text
schema version
output name
source artifact paths
grid identity
layout identity
ordered candidate records
tile identities
pixel windows
spatial bounds
label counts
```

Real catalog identity:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

A meaningful catalog-content change produces a different identity.

### L1-7C.5 — Canonical Persistence and Verification

Implemented:

```text
tile_catalog_to_dict
write_tile_catalog
verify_tile_catalog_artifact
```

Persistence uses:

```text
UTF-8 JSON
sorted object keys
deterministic tile order
finite numeric values
one final newline
```

Verification compares the physical JSON artifact with the complete expected in-memory representation.

The verifier detects missing, malformed, or modified artifacts.

### L1-7C.6 — Real Catalog Construction

Generated the real artifact:

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

Measured output:

```text
schema version: tile-catalog-v1
file size: 815,877 bytes
tile count: 870
supervised tiles: 50
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
```

Physical artifact SHA-256:

```text
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6
```

Two consecutive executions produced identical physical hashes:

```text
True
```

Artifact verification result:

```text
PASS: Real candidate tile catalog was written and verified.
```

## Label Semantics

The catalog preserves:

```text
POSITIVE = 1
NEGATIVE = 0
IGNORE = 255
```

Candidate classification is:

```text
positive
negative_only
all_ignore
```

An all-ignore tile is not a negative tile.

Therefore:

```text
UNLABELED != NEGATIVE
```

remains preserved after tiling.

The catalog classification is derived from raster values.

It does not merge or replace source provenance.

Ordinary negative and hard-negative provenance remains available from the vector sources for use during sampling.

## Final L1-7 Runtime Flow

The complete L1-7 flow is:

```text
real aligned image and label rasters
↓
exact shared raster grid
↓
tiling contracts and validation
↓
stable layout identity
↓
evidence-based layout selection
↓
deterministic tile-window generation
↓
stable tile-window identities
↓
candidate geometry analysis
↓
label-aware analysis
↓
positive-feature containment analysis
↓
approved Loop 1 tiling policy
↓
per-window label and spatial measurements
↓
complete candidate tile catalog
↓
stable catalog identity
↓
canonical JSON persistence
↓
physical artifact verification
```

## Final L1-7 Outputs

### Selected Policy

```text
256 × 256 pixels
192-pixel stride
25% overlap
SHIFT_TO_FIT
```

### Candidate Population

```text
870 complete deterministic candidates
```

### Persistent Artifact

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

### Stable Identities

Grid:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

Layout:

```text
sha256:5c4baabc2477f27ee08f921b681e8ea56a5eef3b45cdd2d3bcb98cb76637f602
```

Catalog:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

Physical catalog file:

```text
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6
```

## Implementation

Primary package:

```text
src/geoai_dataset_curation/tiling/
```

Modules:

```text
contracts.py
validation.py
identity.py
policy.py
window_generation.py
analysis.py
label_analysis.py
catalog.py
catalog_generation.py
catalog_identity.py
catalog_io.py
```

Real execution scripts:

```text
scripts/check_real_tiling_layout_geometry.py
scripts/check_real_tile_label_analysis.py
scripts/check_real_positive_reference_scale.py
scripts/check_real_positive_tile_containment.py
scripts/build_real_tile_catalog.py
```

Automated tests:

```text
tests/test_tiling_contracts.py
tests/test_tiling_validation.py
tests/test_tile_identity.py
tests/test_tile_window_generation.py
tests/test_tile_layout_analysis.py
tests/test_tile_label_analysis.py
tests/test_loop1_tiling_policy.py
tests/test_tile_catalog_contracts.py
tests/test_tile_catalog_generation.py
tests/test_tile_catalog_persistence.py
```

## Decision Records

```text
DR-0012 — Define a Deterministic Tiling Contract Boundary
DR-0013 — Select the Loop 1 Tiling Policy
DR-0014 — Persist the Candidate Tile Catalog Before Sampling
```

## Evidence Records

```text
docs/evidence/loop1_increment_15_tiling_policy_analysis.md
docs/evidence/loop1_increment_16_real_candidate_tile_catalog.md
```

## Validation Summary

```text
tiling contracts: PASS
layout validation: PASS
stable tile identities: PASS
deterministic window generation: PASS
real geometry analysis: PASS
real label-aware analysis: PASS
positive-reference scale analysis: PASS
actual feature containment: PASS
selected policy validation: PASS
catalog contracts: PASS
catalog validation: PASS
catalog generation: PASS
catalog identity: PASS
canonical persistence: PASS
artifact verification: PASS
physical rerun determinism: PASS
focused catalog tests: 19 passed
complete test suite: 394 passed
git diff --check: clean
```

## Architectural Boundary

L1-7 produces candidate records only.

It does not produce final training pairs.

The next phase receives:

```text
verified candidate tile catalog
+
real image raster
+
real label raster
+
reference-source provenance
```

The next phase is responsible for:

```text
sampling policy
positive selection
ordinary-negative selection
hard-negative prioritization
all-ignore handling
physical image tile extraction
physical label tile extraction
pair verification
```

## Deferred Responsibilities

The following remain outside L1-7:

```text
L1-8  — Sampling and Pair Generation
L1-9  — Quality Control
L1-10 — Spatial Split
L1-11 — Manifest and Dataset Version
L1-12 — Training Package
```

Spatial split assignment is intentionally deferred.

Tile overlap creates related observations, so split assignment must operate with explicit spatial controls rather than independently assigning overlapping tiles.

## Closure Criteria

```text
Code works: PASS
Tests pass: PASS
Artifact exists: PASS
Decision documented: PASS
Evidence measurable: PASS
Artifact deterministic: PASS
Artifact verified: PASS
Scope boundary preserved: PASS
```

## Closure Decision

L1-7C is complete.

L1-7 — Tiling is complete.

The project now has:

- one approved Loop 1 tiling policy
- one complete deterministic candidate population
- stable tile and catalog identities
- per-candidate spatial and label metadata
- one persistent verified candidate catalog
- a clean boundary for sampling and pair generation

The project is ready to begin:

```text
L1-8 — Sampling and Pair Generation
```