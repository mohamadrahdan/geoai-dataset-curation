# Loop 1 Increment 14 — Real Label Manifest Evidence

## Scope

This evidence record documents the persistent machine-readable manifest for the real Loop 1 label artifact.

The manifest records provenance, spatial identity, supervision semantics, source contributions, pixel statistics, and verified image-label alignment.

## Physical Artifacts

Label raster:

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

Image raster:

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

Label manifest:

```text
artifacts/live/loop1/komeh_labels_v1.manifest.json
```

## Manifest Identity

The manifest records:

```text
manifest_version: 1.0
output_name: komeh_labels_v1
CRS: EPSG:32639
width: 5712
height: 5493
dtype: uint8
band_count: 1
allowed_values: [0, 1, 255]
```

The raster is associated with the approved shared grid:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

## Supervision Sources

The manifest records three real reference sources.

### Positive Reference

```text
source_id: landslide-reference
supervision: positive_reference
feature_count: 57
repaired_feature_count: 1
covered_pixel_count: 17,933
```

### Negative Reference

```text
source_id: negative-reference
supervision: negative_reference
feature_count: 54
repaired_feature_count: 1
covered_pixel_count: 23,640
```

### Hard-Negative Reference

```text
source_id: hard-negative-reference
supervision: hard_negative_reference
feature_count: 49
repaired_feature_count: 0
covered_pixel_count: 40,751
```

The complete reference inventory contains:

```text
160 features
```

## Pixel Statistics

The manifest records:

```text
total_pixels:      31,376,016
supervised_pixels:     82,321
positive_pixels:       17,933
negative_pixels:       64,388
ignore_pixels:     31,293,695
```

The persisted values therefore preserve the supervision semantics:

```text
0   -> NEGATIVE
1   -> POSITIVE
255 -> IGNORE
```

## Provenance Overlap

The manifest records the verified same-target overlap between negative and hard-negative supervision:

```text
negative_hard_negative_overlap_pixels: 3
```

This is valid because both supervision sources map to:

```text
NEGATIVE = 0
```

while their provenance remains distinct.

## Image–Label Relationship

The manifest explicitly records:

```text
image_label_alignment_verified: true
```

The physical image and label rasters were previously verified to share the same:

```text
CRS
width
height
affine transform
pixel origin
```

## Validation

The generated manifest was serialized to JSON and reloaded for validation.

Observed checks:

```text
manifest_version: True
grid_id: True
artifact_path: True
alignment: True
allowed_values: True
source_count: True
feature_count: True
pixel_total: True
supervised_pixels: True
```

Final result:

```text
PASS
```

## Architectural Result

The real label artifact is no longer represented only by a physical GeoTIFF.

It now has a persistent machine-readable provenance record:

```text
real references
↓
validated and repaired vectors
↓
exact-grid rasterization
↓
physical label GeoTIFF
↓
spatial QC and pixel statistics
↓
direct image-label alignment verification
↓
persistent label manifest
```

## Measurable Evidence

The increment establishes:

```text
1 real label GeoTIFF
1 persistent label manifest
3 supervision sources
160 reference features
2 repaired geometries
31,376,016 total raster pixels
82,321 supervised pixels
3 same-target provenance overlap pixels
verified shared grid
verified image-label alignment
manifest validation PASS
```

## Scope Boundary

The manifest records the current real label artifact and its provenance.

It does not yet define:

```text
training tiles
dataset splits
sampling strategy
model configuration
training metrics
```

Those belong to subsequent dataset-construction and training stages.