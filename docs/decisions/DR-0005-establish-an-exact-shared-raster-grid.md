# DR-0005: Establish an Exact Shared Raster Grid

## Status

Accepted

## Context

The Dataset Curation pipeline must eventually construct Sentinel-2 image rasters and rasterized labels that align exactly.

Matching only the coordinate reference system and nominal pixel resolution is insufficient. Two rasters can share the same CRS, width, height, and pixel size while having different origins. Even a one-pixel shift would make the image and label arrays spatially inconsistent and would reduce the reliability of segmentation training inputs.

The previous image-construction contract represented:

- CRS
- width
- height
- horizontal pixel size
- vertical pixel size

It did not represent the complete affine transform required to define the exact location and orientation of the raster grid.

The real Earth Engine construction path also needs an explicit export contract that can be mapped to:

- `crs`
- `crsTransform`
- raster dimensions
- raster bounds

## Decision

The exact raster grid is represented by `RasterGridSpec` together with a separate `AffineTransformSpec`.

`AffineTransformSpec` stores six coefficients in the following order:

```text
(a, b, c, d, e, f)
```

This order matches both:

```text
Rasterio Affine(a, b, c, d, e, f)
Earth Engine crsTransform = [a, b, c, d, e, f]
```

For the Loop 1 north-up raster contract:

- `a` is the positive horizontal pixel size.
- `b` must be zero.
- `c` is the upper-left x coordinate.
- `d` must be zero.
- `e` is the negative vertical pixel size.
- `f` is the upper-left y coordinate.

The generic `RasterGridSpec` keeps its transform optional for backward compatibility with the earlier image-construction contract.

A separate strict validator, `validate_exact_raster_grid_spec`, requires the affine transform when the grid is used for exact raster export.

The strict Loop 1 export contract accepts only north-up grids:

- `a > 0`
- `e < 0`
- `b = 0`
- `d = 0`
- `abs(a) = pixel_size_x`
- `abs(e) = pixel_size_y`

Every complete grid receives a deterministic SHA-256 `grid_id` derived from a canonical representation containing:

- schema version
- CRS
- width
- height
- pixel sizes
- affine-transform coefficients

The exact grid can also be converted into:

- derived raster bounds
- Earth Engine export parameters
- a traceable image-construction manifest

## Consequences

### Positive consequences

- Image construction and label rasterization can refer to the same exact grid.
- A one-pixel origin shift produces a different `grid_id`.
- Grid equality no longer depends only on CRS and nominal resolution.
- Earth Engine export parameters can be derived deterministically.
- Raster bounds can be derived from the same approved grid definition.
- Construction manifests record the exact spatial contract.
- The grid contract can later be verified against a downloaded GeoTIFF using Rasterio.
- The earlier image-construction contract remains backward compatible.

### Negative consequences

- Loop 1 intentionally rejects rotated or sheared raster grids.
- Exact-grid validation introduces a stricter path in addition to generic grid validation.
- Grid identity depends on the canonical schema version and must be versioned carefully if the identity representation changes.
- A valid contract does not yet prove that an exported GeoTIFF actually matches the requested grid. Artifact verification remains a later increment.

## Alternatives considered

### Store loose origin fields directly in `RasterGridSpec`

Rejected because the raster grid is more accurately and consistently represented by a standard six-parameter affine transform.

### Use only CRS and pixel resolution

Rejected because these values do not identify the raster origin, orientation, dimensions, or exact pixel footprint.

### Make the affine transform mandatory for every grid immediately

Rejected because it would break the backward-compatible L1-5A construction contract. Exact export therefore uses a dedicated stricter validator.

### Support rotated and sheared grids in Loop 1

Deferred because the Padena Sentinel-2 dataset requires a north-up raster grid. Supporting arbitrary affine orientation would increase complexity without adding value to the first complete loop.

### Use a manually assigned grid name as identity

Rejected because a human-readable name does not prove that two complete spatial grid definitions are identical.

## Evidence

The implementation includes focused tests for:

- exact affine-transform storage
- coefficient ordering
- backward compatibility without a transform
- finite affine coefficients
- north-up orientation
- transform and pixel-size consistency
- mandatory transform for exact export
- positive x scale and negative y scale
- deterministic grid identity
- one-pixel origin-shift detection
- CRS-change detection
- exact transform serialization in manifests
- derived raster bounds
- Earth Engine export parameter serialization
- invalid-grid rejection

At Increment 1 closure, the complete automated test suite contains 90 passing tests.

## Scope boundary

This decision establishes the exact shared-grid contract.

It does not yet:

- authenticate with Earth Engine
- query Sentinel-2 imagery
- construct a cloud-masked composite
- start an Earth Engine export task
- download a GeoTIFF
- verify an exported raster with Rasterio
- rasterize labels

Those responsibilities belong to later L1-5B increments.