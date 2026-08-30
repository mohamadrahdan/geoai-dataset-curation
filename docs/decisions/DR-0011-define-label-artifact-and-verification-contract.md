# DR-0011: Define the Label Artifact and Verification Contract

## Status

Accepted

## Context

Loop 1 now defines:

- label supervision semantics
- the vector-to-label-raster input boundary
- the rasterization policy
- the exact shared raster grid

Before real label rasterization begins, the expected physical label artifact must also be explicit.

A generated label file is not valid merely because it exists.

For segmentation training, a label raster must satisfy both spatial and semantic requirements.

The spatial requirements include:

```text
CRS
width
height
affine transform
```

The label-specific requirements include:

```text
single band
uint8 dtype
allowed values only
```

The Loop 1 label values are:

```text
0   = explicit negative target
1   = positive landslide target
255 = ignore
```

The verification contract must therefore detect both spatial misalignment and invalid label encoding.

## Decision

Introduce an explicit expected-artifact contract:

```text
LabelRasterArtifactSpec
```

The Loop 1 artifact contract requires:

```text
band_count     = 1
dtype          = uint8
allowed_values = {0, 1, 255}
grid           = approved exact shared grid
```

The artifact specification is created from a validated label-rasterization request.

The approved raster grid remains authoritative.

The label artifact does not create or redefine its own spatial grid.

## Verification

Physical label artifacts will be verified through:

```text
LabelRasterVerificationResult
```

Verification checks:

```text
CRS
width
height
affine transform
band count
dtype
observed pixel values
```

Spatial verification reuses the existing raster-grid verification capability rather than introducing a second implementation.

A label raster passes only when all checks pass.

Conceptually:

```text
Spatial Contract
+
Label Encoding Contract
↓
Valid Label Artifact
```

A correct dtype or set of pixel values cannot compensate for a spatial mismatch.

Likewise, exact spatial alignment cannot compensate for invalid label values.

## Allowed Pixel Values

The valid Loop 1 values are derived from the shared `LabelValue` contract.

The expected values are:

```text
NEGATIVE = 0
POSITIVE = 1
IGNORE   = 255
```

Unexpected values such as:

```text
2
3
254
```

must cause verification failure unless a later version of the label contract explicitly introduces them.

## Data Type

Loop 1 label rasters use:

```text
uint8
```

This is sufficient to represent all current categorical label values, including the ignore value of `255`.

The label raster is categorical training data and does not require the floating-point representation used by continuous image rasters.

## Band Count

A Loop 1 label raster must contain exactly one band.

The single band represents the training target mask.

Multi-band label artifacts are rejected by the current contract.

## Architectural Boundary

The intended flow is:

```text
LabelRasterizationRequest
↓
LabelRasterArtifactSpec
↓
Future Physical Rasterization
↓
Raster Metadata Inspection
+
Observed Label Values
↓
Label Artifact Verification
```

L1-6A defines the expected contract and verification behavior only.

It does not yet create a physical label GeoTIFF.

Physical execution belongs to L1-6B.

## Reuse of Existing Raster Infrastructure

The image-construction workflow already provides generic raster metadata inspection and exact-grid verification.

This decision reuses that infrastructure for label rasters.

The existing spatial verification checks:

```text
CRS
width
height
affine transform
```

The label-rasterization layer adds only label-specific checks:

```text
band count
dtype
allowed values
```

This avoids duplicating spatial verification logic.

## Consequences

### Positive consequences

- label artifacts have an explicit machine-testable contract
- image and label rasters can rely on the same exact-grid definition
- one-pixel spatial shifts are detectable
- invalid categorical values are detectable
- incorrect raster dtype is detectable
- accidental multi-band masks are rejected
- generic raster verification logic is reused
- real rasterization in L1-6B has a clear acceptance boundary

### Trade-offs

- Loop 1 currently supports only one-band uint8 labels
- the allowed-value schema is intentionally strict
- verification of actual unique pixel values requires reading the physical raster during execution
- additional output classes would require a versioned contract change

## Alternatives Considered

### Accept any integer raster dtype

Rejected because the current label range fits cleanly in uint8 and a fixed dtype makes the artifact contract simpler and more reproducible.

### Verify only spatial metadata

Rejected because a perfectly aligned raster may still contain invalid training labels.

### Verify only label values

Rejected because valid values on a shifted grid would still create incorrect image-label pairs.

### Build separate spatial verification for labels

Rejected because the existing exact-grid verification already provides the required checks.

### Create the real label manifest during L1-6A

Deferred.

A real label manifest should describe actual execution evidence such as:

```text
physical artifact path
real source identities
observed class values
class statistics
real grid verification
rasterization execution result
```

Those values do not exist until L1-6B performs real rasterization.

## Evidence

The implementation includes:

```text
LabelRasterArtifactSpec
LOOP1_LABEL_ALLOWED_VALUES
create_label_raster_artifact_spec
validate_label_raster_artifact_spec
LabelRasterVerificationResult
verify_label_raster_artifact
```

Focused tests verify:

- Loop 1 allowed label values
- artifact-spec creation from a rasterization request
- single-band enforcement
- uint8 enforcement
- rejection of unexpected allowed values
- successful verification of a valid artifact
- detection of unexpected observed pixel values
- detection of incorrect dtype
- detection of incorrect band count
- detection of an affine-transform shift

At the time of this decision:

```text
11 focused label-artifact tests pass
295 total tests pass
git diff --check is clean
```

## Scope Boundary

This decision completes the contract side of label rasterization.

It does not yet:

- rasterize real reference polygons
- write a label GeoTIFF
- inspect real class counts
- verify a real label artifact
- compare the physical image and label rasters
- create a real label manifest

Those responsibilities belong to L1-6B.