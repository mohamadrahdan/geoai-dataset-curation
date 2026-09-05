# Loop 1 Increment 13 — Label Statistics and Spatial QC Evidence

## Scope

This evidence record documents pixel-level label statistics and spatial quality control for the real Loop 1 supervision.

The increment verifies that the real reference geometries produce usable raster supervision on the approved exact grid and measures the resulting class distribution.

## Physical Label Artifact

The analyzed label raster is:

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

The raster contains:

```text
31,376,016 total pixels
```

## Pixel-Level Supervision Statistics

Observed values:

```text
NEGATIVE = 0
POSITIVE = 1
IGNORE   = 255
```

Measured pixel counts:

```text
Negative pixels:   64,388
Positive pixels:   17,933
Ignore pixels: 31,293,695
```

The total supervised pixel count is:

```text
82,321
```

The supervised fraction of the full raster is:

```text
0.262369%
```

Within the supervised pixels:

```text
Positive: 21.784235%
Negative: 78.215765%
```

These statistics reflect explicit supervision only.

Pixels without explicit reference supervision remain:

```text
IGNORE = 255
```

and are not interpreted as negative background.

## Source-Level Spatial QC

### Landslide Reference

```text
Features: 57
Covered pixels: 17,933
Zero-pixel features: 0
Partially outside features: 0
Disjoint features: 0
```

### Negative Reference

```text
Features: 54
Covered pixels: 23,640
Zero-pixel features: 0
Partially outside features: 0
Disjoint features: 0
```

### Hard-Negative Reference

```text
Features: 49
Covered pixels: 40,751
Zero-pixel features: 0
Partially outside features: 0
Disjoint features: 0
```

## Vector-to-Raster Coverage Result

All real reference geometries produced raster supervision:

```text
160 total reference features
160 features with raster contribution
0 zero-pixel features
0 partially outside features
0 disjoint features
```

No real reference geometry was lost because of the pixel-center rasterization rule.

## Same-Target Provenance Overlap

The negative-reference and hard-negative-reference sources overlap by:

```text
3 pixels
```

Their separate source contributions are:

```text
negative-reference:      23,640 pixels
hard-negative-reference: 40,751 pixels
```

Their summed contribution is:

```text
64,391 pixels
```

while the final negative target contains:

```text
64,388 pixels
```

The difference is explained by the verified:

```text
3-pixel overlap
```

This overlap is valid because both sources map to the same training target:

```text
NEGATIVE = 0
```

The two sources remain semantically distinct through supervision provenance even though they share the same raster target value.

## Out-of-Grid Policy Enforcement

The execution path now explicitly enforces the approved policy:

```text
partially outside -> allowed and clipped
fully outside     -> rejected
```

The real Loop 1 references contain:

```text
0 fully outside geometries
```

## Verification Result

```text
PASS
```

The real supervision therefore satisfies the current Loop 1 spatial quality-control requirements.

## Architectural Result

The increment proves this relationship:

```text
reference vectors
↓
exact-grid rasterization
↓
source-level spatial QC
↓
pixel-level label statistics
↓
verified supervised training signal
```

The analysis distinguishes:

```text
training target
from
supervision provenance
```

and preserves the rule:

```text
UNLABELED != NEGATIVE
```

## Measurable Evidence

The increment establishes:

```text
31,376,016 total raster pixels
82,321 supervised pixels
0.262369% supervised coverage
17,933 positive pixels
64,388 negative pixels
31,293,695 ignore pixels
160 / 160 reference features contributing raster pixels
0 zero-pixel features
0 partially outside features
0 disjoint features
3 same-target negative provenance overlap pixels
```

## Scope Boundary

This increment measures the current spatial supervision state.

It does not yet define:

```text
tile sampling
train-validation-test splitting
class-balancing strategy
loss weighting
hard-negative sampling frequency
```

Those decisions belong to later dataset-construction and training stages.