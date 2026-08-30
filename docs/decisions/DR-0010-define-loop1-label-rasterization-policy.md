# DR-0010: Define the Loop 1 Label Rasterization Policy

## Status

Accepted

## Context

Loop 1 now has:

- explicit supervision semantics
- a vector-to-label-raster contract
- an exact shared raster grid

The remaining ambiguity is how validated polygons should become raster pixels.

Several rasterization choices can change the resulting label geometry:

- pixel-center vs all-touched inclusion
- overlap resolution
- behavior at the raster boundary
- initial raster fill value

These choices must be explicit before real labels are generated.

The policy must also preserve the earlier rule:

```text
UNLABELED != NEGATIVE
```

Therefore, unlabeled pixels must not default to the negative training target.

## Decision

Loop 1 uses the following rasterization policy:

```text
pixel inclusion     -> pixel center
initial fill        -> IGNORE = 255
conflicting overlap -> error
partial outside     -> clip to grid
fully outside       -> reject
```

### Pixel inclusion

Loop 1 uses the pixel-center rule.

A pixel is labeled by a polygon only when the pixel center satisfies the rasterization membership rule.

The `all_touched` behavior is not used in Loop 1.

This avoids unnecessarily expanding polygon boundaries into neighboring pixels during the baseline dataset construction.

### Initial fill

The label raster is initialized with:

```text
IGNORE = 255
```

Only explicit supervision is burned into the raster.

The resulting conceptual flow is:

```text
IGNORE everywhere
→ burn positive references
→ burn reviewed negatives
→ burn hard negatives
```

The absence of a polygon does not create a negative target.

### Overlap policy

Conflicting supervision must never be resolved silently.

Loop 1 does not use:

```text
last source wins
```

or any similar implicit precedence rule.

If incompatible supervision would assign conflicting targets to the same raster location, rasterization must fail or report the conflict explicitly.

Overlaps that do not create a semantic contradiction may be handled without changing the numeric target, but supervision provenance must not be silently discarded.

### Out-of-grid behavior

A geometry that partially intersects the approved raster grid may be clipped to the grid extent.

A geometry that is fully disjoint from the raster grid is not valid rasterization input and must be rejected or reported.

The rasterization layer does not expand or rebuild the approved grid to accommodate reference geometry.

## Contract

The policy is represented by:

```text
LabelRasterizationPolicy
PixelInclusionRule
OverlapRule
OutOfGridRule
```

The default Loop 1 policy is:

```text
LOOP1_RASTERIZATION_POLICY
```

The policy is carried by `LabelRasterizationRequest` so the rasterization behavior becomes part of the request contract and can later be persisted in provenance metadata.

## Architectural Boundary

The flow is:

```text
Validated Explicit Supervision
+
Exact Shared Raster Grid
+
Rasterization Policy
↓
Validated LabelRasterizationRequest
↓
Future Rasterization Execution
```

This increment defines behavior only.

It does not yet execute physical rasterization.

## Consequences

### Positive consequences

- unlabeled pixels remain ignored by default
- polygon-to-pixel behavior is deterministic
- conflicting labels cannot be silently overwritten
- the raster grid remains authoritative
- boundary handling is explicit
- rasterization behavior can later be stored in manifests
- the contract remains testable before real label generation

### Trade-offs

- the policy is intentionally strict
- fully disjoint reference geometries cannot be silently ignored
- future scientific evidence may justify another pixel-inclusion strategy
- overlap detection still requires a concrete rasterization implementation
- provenance-aware handling of non-conflicting overlaps remains an execution concern

## Alternatives Considered

### Use `all_touched=True`

Not selected for the Loop 1 baseline because it can expand polygon coverage into neighboring pixels and change class-area statistics.

It may be evaluated later if model or annotation evidence justifies it.

### Initialize the raster with `NEGATIVE = 0`

Rejected because the reference inventory is incomplete.

Unannotated areas are not reliable negative evidence.

### Use last-source-wins overlap resolution

Rejected because the result would depend on source order and could silently hide contradictory supervision.

### Ignore geometries outside the raster grid

Rejected as the default policy because a fully disjoint reference source may indicate an upstream CRS, extent, or source-selection problem that should remain visible.

## Evidence

The implementation includes:

```text
LabelRasterizationPolicy
LOOP1_RASTERIZATION_POLICY
PixelInclusionRule
OverlapRule
OutOfGridRule
validate_label_rasterization_policy
```

The rasterization request now carries the policy and validates it together with the supervision sources and exact grid.

Focused tests verify:

- pixel-center inclusion
- IGNORE initialization
- explicit overlap-conflict policy
- partial clipping and disjoint rejection policy
- default Loop 1 policy stability
- rejection of negative fill values
- rejection of positive fill values
- successful integration with a valid rasterization request

At the time of this decision:

```text
17 focused rasterization-policy tests pass
284 total tests pass
git diff --check is clean
```

## Deferred Decisions

The next increment will define the label artifact and verification contracts.

Physical rasterization execution remains outside L1-6A and belongs to L1-6B.