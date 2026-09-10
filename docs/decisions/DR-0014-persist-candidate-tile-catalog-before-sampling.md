# DR-0014: Persist the Candidate Tile Catalog Before Sampling

## Status

Accepted

## Context

Loop 1 now has:

- a real Sentinel-2 image
- a real aligned label raster
- an exact shared raster grid
- deterministic tile-window generation
- stable tile identities
- an evidence-based tiling policy

The selected layout is:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 25%
edge policy: SHIFT_TO_FIT
```

This layout produces:

```text
870 deterministic candidate windows
```

Before sampling begins, the complete candidate population must be recorded.

Without a persistent candidate catalog, later sampling would depend on an implicit runtime population. That would make it harder to answer:

- which tiles were eligible for sampling
- which grid and layout produced them
- which tile identities existed before filtering
- which tiles contained positive or negative supervision
- whether rerunning tiling produced the same population
- whether the sampled dataset can be traced back to its complete candidate set

The project therefore needs an explicit boundary between:

```text
candidate generation
```

and:

```text
sample selection
```

## Decision

Loop 1 persists the complete deterministic candidate tile population before sampling.

The persistent artifact is:

```text
artifacts/live/loop1/komeh_candidate_tiles_v1.catalog.json
```

The catalog contains all 870 candidate windows.

No candidate is removed because of its label composition during L1-7.

The catalog is created before:

- positive and negative balancing
- hard-negative sampling
- all-ignore exclusion
- physical image-label pair generation
- spatial split assignment

## Catalog Contract

The catalog uses:

```text
schema version: tile-catalog-v1
```

Top-level fields include:

```text
catalog_id
schema_version
output_name
image_artifact_path
label_artifact_path
grid_id
layout_id
tile_count
tiles
```

Each candidate record includes:

```text
tile_id
grid_id
layout_id
row_index
column_index
row_offset_pixels
column_offset_pixels
read_width_pixels
read_height_pixels
output_width_pixels
output_height_pixels
left
bottom
right
top
positive_pixel_count
negative_pixel_count
ignore_pixel_count
label_class
output_pixel_count
read_pixel_count
padding_pixel_count
supervised_pixel_count
```

## Stable Identity

Each tile retains the stable identity established by the tiling contract.

The complete catalog also receives a semantic SHA-256 identity.

The catalog identity is derived from canonical content containing:

- schema version
- output name
- image artifact path
- label artifact path
- grid identity
- layout identity
- ordered candidate records
- tile-window identities
- spatial bounds
- label counts

The catalog identity does not depend on JSON indentation or filesystem metadata.

The real Loop 1 catalog identity is:

```text
sha256:3cea6168c45657427efe3f28c60fa9029254ff2587771eed95d0c7291bb5bd28
```

## Deterministic Ordering

Candidate records are stored in deterministic row-major order.

The ordering key is:

```text
(row_index, column_index)
```

The catalog contract rejects:

- duplicate tile identities
- duplicate row-column positions
- non-row-major ordering
- record grid-identity mismatches
- record layout-identity mismatches

This ensures that repeated construction produces the same logical catalog and the same serialized artifact.

## Label-Derived Candidate Classes

Each candidate receives one label-derived class.

The classification rule is:

```text
positive pixels > 0
    -> positive

positive pixels = 0 and negative pixels > 0
    -> negative_only

positive pixels = 0 and negative pixels = 0
    -> all_ignore
```

The real catalog contains:

```text
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
```

These classes describe raster-label composition only.

They do not replace supervision provenance.

In particular:

```text
negative training target
!=
negative-source provenance
```

Ordinary negative references and hard-negative references both use raster value zero. Their provenance distinction cannot be reconstructed from label values alone.

That distinction remains available from the vector sources and will be applied during sampling.

## Unlabeled Semantics

The catalog preserves the core rule:

```text
UNLABELED != NEGATIVE
```

A candidate containing only ignore pixels is classified as:

```text
all_ignore
```

It is not classified as a negative tile.

Whether all-ignore candidates are excluded, retained, or used for another purpose is a sampling decision and is not performed during tiling.

## Complete Candidate Population

The catalog intentionally includes all deterministic windows:

```text
total candidates: 870
supervised candidates: 50
unsupervised all-ignore candidates: 820
```

Persisting the full population allows later stages to document exactly:

- which candidates were eligible
- which candidates were selected
- which candidates were rejected
- why each sampling decision occurred

## Persistence Format

Loop 1 uses one formatted JSON document.

Serialization uses:

```text
UTF-8 encoding
sorted object keys
deterministic record ordering
finite numeric values
one final newline
```

The selected format is appropriate for the current population of 870 records.

The real artifact size is:

```text
815,877 bytes
```

## Verification

The persisted artifact is compared with the expected in-memory catalog.

Verification detects:

- missing artifact
- invalid UTF-8 or JSON
- changed metadata
- changed tile count
- changed tile ordering
- changed tile identity
- changed spatial bounds
- changed label counts
- any other serialized content mismatch

The verified physical file SHA-256 is:

```text
DDBA1667165B0494383C2B0E7C78BEF5B9620DE8CA314EE59CD4D452987C5FB6
```

Two consecutive real executions produced the same physical file hash:

```text
True
```

## Local Artifact Policy

The real catalog is generated under:

```text
artifacts/live/loop1/
```

The physical artifact remains outside version control under the existing artifact policy.

The repository stores:

- the deterministic contracts
- the catalog builder
- the canonical serializer
- the artifact verifier
- the real execution script
- automated tests
- measurable evidence
- semantic and physical artifact identities

This preserves reproducibility without committing generated live artifacts.

## Architectural Boundary

The completed flow is:

```text
real aligned image and label rasters
+
exact shared grid
+
approved tiling layout
↓
deterministic tile windows
↓
stable tile identities
↓
per-tile spatial and label measurements
↓
complete candidate tile catalog
↓
persistent verified JSON artifact
```

The next boundary is:

```text
verified candidate catalog
+
sampling policy
+
supervision provenance
↓
selected image-label pairs
```

L1-7 does not select or materialize training samples.

## Consequences

### Positive Consequences

- the complete candidate population is explicit
- later sampling is reproducible
- tile eligibility is auditable
- every record is linked to the exact grid and layout
- label composition is available without rereading the raster
- all-ignore tiles remain distinct from negative-only tiles
- catalog identity changes when meaningful content changes
- physical serialization is deterministic
- later manifests can reference one stable catalog identity
- sampling decisions can be compared against the complete population

### Trade-offs

- the catalog repeats some grid and layout identities per record
- the JSON artifact is larger than a minimal window-only representation
- label counts must be regenerated when the label raster changes
- catalog identity depends on artifact paths as well as tile content
- the complete catalog includes many candidates that may never be sampled
- ordinary-negative and hard-negative provenance still requires vector-source analysis

## Alternatives Considered

### Sample During Tile Generation

Rejected.

Combining generation and sampling would hide the complete candidate population and make later sampling decisions harder to audit.

### Persist Only Supervised Tiles

Rejected.

This would remove all-ignore candidates before the sampling policy is defined and would mix tiling responsibilities with sampling decisions.

### Treat All-Ignore Tiles as Negative

Rejected.

This would violate:

```text
UNLABELED != NEGATIVE
```

### Materialize Physical Tile Pairs During L1-7

Rejected.

Physical image-label pair creation belongs to L1-8 after the sampling policy selects the required candidates.

### Use JSON Lines

Not selected for Loop 1.

The current population is small enough for one validated JSON document. Whole-catalog serialization also supports straightforward semantic identity and exact artifact comparison.

JSON Lines may become useful in a larger future loop.

### Store the Catalog in a Database

Not selected for Loop 1.

A database would add unnecessary operational complexity for 870 deterministic records. The current JSON artifact is sufficient for local reproducibility and later dataset construction.

## Implementation Evidence

The implementation includes:

```text
TileCandidateRecord
TileCatalog
TileLabelClass
validate_tile_candidate_record
validate_tile_catalog
build_tile_catalog
build_tile_catalog_id
tile_catalog_identity_payload
tile_catalog_to_dict
write_tile_catalog
verify_tile_catalog_artifact
```

Real execution is provided by:

```text
scripts/build_real_tile_catalog.py
```

Automated tests cover:

- candidate label-class derivation
- pixel-count consistency
- grid and layout identity consistency
- unique tile identities
- unique tile positions
- deterministic row-major ordering
- stable catalog identity
- identity sensitivity to content changes
- canonical serialization
- physical writing
- artifact verification
- modified-artifact detection
- real window-to-record construction
- deterministic repeated construction
- edge-padding accounting

At the time of this decision:

```text
19 focused catalog tests pass
394 total tests pass
git diff --check is clean
```

## Scope Boundary

This decision completes deterministic candidate-catalog persistence.

It does not:

- define sampling ratios
- select the final subset
- distinguish hard negatives from ordinary negatives spatially
- extract physical raster tiles
- assign training, validation, or test splits
- publish the final dataset manifest

Those responsibilities remain in:

```text
L1-8  — Sampling and Pair Generation
L1-10 — Spatial Split
L1-11 — Manifest and Dataset Version
```

## Decision Summary

Loop 1 persists the complete deterministic candidate tile population before any sampling occurs.

The resulting catalog is:

```text
complete
label-aware
identity-stable
row-major ordered
canonically serialized
physically reproducible
independently verifiable
```

This creates a clean and auditable boundary between tiling and sampling.