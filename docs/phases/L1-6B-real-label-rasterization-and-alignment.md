# L1-6B — Real Label Rasterization and Alignment

## Objective

The objective of L1-6B was to convert the approved Loop 1 label-rasterization contracts into a real, validated, spatially aligned, and reproducible label artifact.

The phase connects private real reference polygons to the approved Sentinel-2 raster grid and produces the first physical Loop 1 training-label raster.

## Completed Increments

### L1-6B.1 — Real Reference Label Wiring

Completed:

```text
real reference environment wiring
real vector loading
controlled invalid-geometry repair
post-repair validation
reprojection to the approved target CRS
runtime LabelVectorSource construction
```

Measured real inputs:

```text
57 positive-reference features
54 negative-reference features
49 hard-negative-reference features
160 total features
```

Geometry repair:

```text
2 invalid self-intersections detected
2 geometries repaired
0 features dropped
```

### L1-6B.2 — Real Label Rasterization

Completed:

```text
real vector-to-raster execution
pixel-center rasterization
IGNORE initialization
same-target overlap handling
conflicting-target rejection
physical GeoTIFF writing
label artifact verification
```

Generated artifact:

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

Verified properties:

```text
CRS: EPSG:32639
width: 5712
height: 5493
dtype: uint8
band_count: 1
allowed values: {0, 1, 255}
```

### L1-6B.3 — Image–Label Alignment Verification

The physical Sentinel-2 image and physical label raster were compared directly.

Verified:

```text
CRS matches
width matches
height matches
affine transform matches
pixel origin matches
```

Result:

```text
PASS: Physical image and label rasters are exactly pixel-aligned.
```

### L1-6B.4 — Label Statistics and Spatial QC

Measured pixel distribution:

```text
total pixels:      31,376,016
supervised pixels:     82,321
positive pixels:       17,933
negative pixels:       64,388
ignore pixels:     31,293,695
```

Measured supervised distribution:

```text
positive: 21.784235%
negative: 78.215765%
```

Spatial QC:

```text
160 / 160 features produced raster supervision
0 zero-pixel features
0 partially outside features
0 disjoint features
```

Verified same-target provenance overlap:

```text
negative-reference vs hard-negative-reference: 3 pixels
```

### L1-6B.5 — Real Label Manifest and Closure

Generated persistent manifest:

```text
artifacts/live/loop1/komeh_labels_v1.manifest.json
```

The manifest records:

```text
artifact identity
shared grid identity
supervision source provenance
feature counts
repair counts
pixel statistics
allowed values
image-label alignment status
same-target provenance overlap
```

Manifest validation:

```text
PASS
```

## Final Runtime Flow

The completed L1-6B runtime path is:

```text
private reference polygons
↓
environment-based runtime wiring
↓
geometry inspection and controlled repair
↓
metadata and geometry validation
↓
reprojection to EPSG:32639
↓
LabelVectorSource
↓
LabelRasterizationRequest
↓
approved rasterization policy
↓
uint8 label array
↓
physical label GeoTIFF
↓
label artifact verification
↓
direct image-label alignment verification
↓
pixel statistics and spatial QC
↓
persistent label manifest
```

## Core Semantic Result

L1-6B preserves the distinction:

```text
training target
!=
supervision provenance
```

Training targets:

```text
POSITIVE -> 1
NEGATIVE -> 0
IGNORE   -> 255
```

Supervision provenance remains distinct:

```text
POSITIVE_REFERENCE
NEGATIVE_REFERENCE
HARD_NEGATIVE_REFERENCE
UNLABELED
NODATA
```

The phase therefore preserves the core rule:

```text
UNLABELED != NEGATIVE
```

## Final Artifacts

```text
artifacts/live/loop1/komeh_labels_v1.tif
artifacts/live/loop1/komeh_labels_v1.manifest.json
```

Supporting evidence:

```text
docs/evidence/loop1_increment_10_real_reference_wiring.md
docs/evidence/loop1_increment_11_real_label_rasterization.md
docs/evidence/loop1_increment_12_image_label_alignment.md
docs/evidence/loop1_increment_13_label_statistics_spatial_qc.md
docs/evidence/loop1_increment_14_real_label_manifest.md
```

## Validation Summary

L1-6B closes with:

```text
real reference wiring: PASS
controlled geometry repair: PASS
real rasterization: PASS
label artifact verification: PASS
image-label alignment: PASS
spatial QC: PASS
label statistics: PASS
persistent manifest: PASS
```

## Closure Decision

L1-6B is complete.

The project now has a real, verified, spatially aligned, semantically controlled label raster that can be used as the basis for subsequent tile construction and training-dataset preparation.

No additional rasterization complexity is required for Loop 1 closure.