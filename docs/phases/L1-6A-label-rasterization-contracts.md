# L1-6A: Label Rasterization Contracts

## Status

Completed

## Objective

Define the semantic, spatial, and artifact contracts required before real reference polygons are converted into a training label raster.

The phase intentionally defines and tests the rasterization boundary without yet creating a physical label GeoTIFF.

## Implemented Work

### 1. Label Schema Contract

The label schema separates supervision semantics from numeric training targets.

The Loop 1 training targets are:

```text
NEGATIVE = 0
POSITIVE = 1
IGNORE   = 255
```

Supervision provenance remains distinct:

```text
POSITIVE_REFERENCE
NEGATIVE_REFERENCE
HARD_NEGATIVE_REFERENCE
UNLABELED
NODATA
```

The key rule is:

```text
UNLABELED != NEGATIVE
```

Unannotated pixels are therefore not automatically treated as negative training evidence.

### 2. Vector-to-Raster Contract

Rasterization accepts only explicit vector supervision:

```text
POSITIVE_REFERENCE
NEGATIVE_REFERENCE
HARD_NEGATIVE_REFERENCE
```

Unlabeled and nodata semantics are not accepted as vector-source inputs.

The rasterization request consumes the approved exact raster grid established during image construction.

### 3. Rasterization Policy Contract

Loop 1 uses the following policy:

```text
pixel inclusion     -> pixel center
initial fill        -> IGNORE = 255
conflicting overlap -> error
partial outside     -> clip to grid
fully outside       -> reject
```

Conflicting supervision is never resolved through an implicit last-source-wins rule.

### 4. Label Artifact and Verification Contract

A valid Loop 1 label raster is expected to be:

```text
one band
uint8
values in {0, 1, 255}
exactly aligned to the approved raster grid
```

Verification checks:

```text
CRS
width
height
affine transform
band count
dtype
allowed pixel values
```

Existing generic raster-grid verification is reused for spatial checks.

## Architectural Flow

The completed contract path is:

```text
Validated Reference Polygons
↓
Supervision Semantics
↓
LabelVectorSource
↓
Exact Shared Raster Grid
+
Rasterization Policy
↓
LabelRasterizationRequest
↓
LabelRasterArtifactSpec
↓
Future Physical Rasterization
↓
Label Artifact Verification
```

## Decisions

The phase is supported by:

- DR-0008: Separate Supervision Semantics from Training Targets
- DR-0009: Define the Vector-to-Label-Raster Contract Boundary
- DR-0010: Define the Loop 1 Label Rasterization Policy
- DR-0011: Define the Label Artifact and Verification Contract

## Practical Verification

Focused tests were added across the four increments for:

- supervision-to-target mapping
- unlabeled-pixel protection
- hard-negative provenance
- vector-source eligibility
- exact-grid requirements
- rasterization policy
- ignore-fill behavior
- artifact structure
- dtype and band count
- allowed label values
- spatial-shift detection

At phase closure:

```text
295 automated tests pass
git diff --check is clean
```

## Observable Artifact

The primary artifacts of L1-6A are the version-controlled contracts and verification rules under:

```text
src/geoai_dataset_curation/label_rasterization/
```

These contracts define the acceptance boundary that the real label GeoTIFF must satisfy in L1-6B.

No physical label raster is produced in L1-6A by design.

## Measurable Evidence

The phase establishes the following explicit guarantees:

```text
unlabeled pixels default to IGNORE
explicit negatives map to 0
positive references map to 1
hard negatives retain distinct provenance
label output is single-band
label output uses uint8
allowed values are exactly {0, 1, 255}
exact-grid mismatch causes verification failure
```

## Limitations

L1-6A does not yet prove execution against the real reference polygons.

The phase does not yet:

- load the real reference sources into the rasterization workflow
- execute polygon rasterization
- write a physical label GeoTIFF
- measure real class-pixel distributions
- inspect real overlap conflicts
- verify real image-label alignment
- create a real-label manifest

These responsibilities are intentionally deferred to L1-6B.

## Completion Checklist

- [x] Label semantics defined
- [x] Partial-inventory behavior defined
- [x] Explicit vector-source boundary defined
- [x] Exact shared grid required
- [x] Rasterization policy defined
- [x] Conflicting-overlap behavior defined
- [x] Label artifact contract defined
- [x] Verification contract defined
- [x] Automated tests pass
- [x] Decisions documented
- [x] Evidence is measurable
- [x] Real execution boundary remains explicit

## Closure

L1-6A is complete.

The system now knows what a valid label raster must mean, how explicit polygon supervision is allowed to enter rasterization, how rasterization must behave, and how the resulting artifact must later be verified.

The next phase is:

```text
L1-6B — Real Label Rasterization and Alignment
```

Its purpose is to execute these contracts against the real reference polygons and produce a physically verified label raster aligned with the real Sentinel-2 image.