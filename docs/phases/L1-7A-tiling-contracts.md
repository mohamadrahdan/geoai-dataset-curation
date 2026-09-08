# L1-7A: Tiling Contracts

## Status

Completed

## Objective

Define the spatial, validation, and identity contracts required before deterministic tile windows are generated from the real aligned image-label raster pair.

This phase establishes the tiling boundary without yet selecting the final Loop 1 tile layout or producing physical training pairs.

## Implemented Work

### 1. Tiling Input Contract

A `TilingRequest` now connects:

```text
image artifact
label artifact
exact shared raster grid
grid identity
tile layout
output identity
```

The image and label paths must be distinct.

The supplied grid identity must match the exact raster-grid specification.

### 2. Tile Layout Contract

A `TileLayoutSpec` explicitly represents:

```text
tile width
tile height
horizontal stride
vertical stride
edge policy
```

The contract rejects:

```text
nonpositive dimensions
nonpositive strides
stride larger than tile dimensions
unsupported edge-policy values
tiles larger than the source grid
```

The supported candidate edge policies are:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

No final Loop 1 policy has yet been selected.

### 3. Tile Window Contract

A `TileWindowSpec` records:

```text
stable tile identity
row and column indices
source pixel offsets
source read dimensions
output dimensions
right padding
bottom padding
partial-window status
```

Window validation rejects:

```text
empty identities
negative indices
negative offsets
nonpositive dimensions
read dimensions larger than output dimensions
output dimensions inconsistent with the layout
windows extending outside the source grid
partial windows away from raster edges
partial windows under non-padding policies
```

### 4. Stable Identity Contract

Canonical SHA-256 identities were introduced for tile layouts and tile windows.

Layout identity includes:

```text
tile dimensions
stride
edge policy
schema version
```

Window identity includes:

```text
grid identity
layout identity
window indices
pixel offsets
read dimensions
schema version
```

Identity-integrity validation detects stale or inconsistent identifiers.

## Architectural Flow

The completed contract path is:

```text
Verified Image-Label Raster Pair
↓
Exact Shared Raster Grid
↓
TilingRequest
↓
TileLayoutSpec
↓
Future Deterministic Window Generator
↓
TileWindowSpec
↓
Window and Identity Validation
↓
Future Candidate Tile Catalog
```

## Practical Verification

Focused tests cover:

- input-contract preservation
- exact-grid requirements
- grid-identity integrity
- tile-layout validation
- spatial-gap rejection
- full-window validation
- padded-edge validation
- raster-boundary protection
- edge-policy compatibility
- stable layout identity
- stable window identity
- identity-change detection

At phase closure:

```text
32 focused tiling tests pass
355 total tests pass
git diff --check is clean
```

## Artifacts

The primary implementation artifacts are:

```text
src/geoai_dataset_curation/tiling/contracts.py
src/geoai_dataset_curation/tiling/identity.py
src/geoai_dataset_curation/tiling/validation.py
src/geoai_dataset_curation/tiling/__init__.py
tests/test_tiling_contracts.py
tests/test_tiling_validation.py
tests/test_tile_identity.py
```

The architectural decision is documented in:

```text
docs/decisions/DR-0012-define-deterministic-tiling-contract-boundary.md
```

## Decisions

L1-7A establishes that:

- tiling is a deterministic spatial-candidate boundary
- tiling remains separate from sampling
- layout parameters must be explicit
- spatial gaps are not accepted
- partial windows require an explicit padding policy
- grid, layout, and window identities must remain connected
- stable identities use canonical SHA-256 payloads

## Measurable Evidence

The phase establishes the following guarantees:

```text
same grid + same layout + same window = same tile identity
material input change = different tile identity
invalid grid identity = rejected request
invalid window identity = rejected window
negative offsets = rejected window
out-of-grid reads = rejected window
implicit spatial gaps = rejected layout
```

## Limitations

L1-7A does not yet:

- select the final tile size
- select the final stride
- select the final overlap
- select the final edge policy
- generate real candidate windows
- compute per-tile label statistics
- create a candidate tile catalog
- write image-label tile pairs
- perform sampling
- assign spatial splits

These responsibilities remain intentionally outside the contract increment.

## Completion Checklist

- [x] Tiling input contract defined
- [x] Tile-layout contract defined
- [x] Tile-window contract defined
- [x] Layout validation implemented
- [x] Window validation implemented
- [x] Stable identity implemented
- [x] Identity-integrity validation implemented
- [x] Tiling remains separate from sampling
- [x] Automated tests pass
- [x] Architectural decision documented
- [x] Evidence is measurable

## Next Phase

The next phase is:

```text
L1-7B — Tile Size, Stride, and Edge Policy
```

Its purpose is to evaluate candidate layouts against the real raster dimensions and supervision distribution before selecting the final Loop 1 tiling policy.