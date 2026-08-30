# DR-0009: Define the Vector-to-Label-Raster Contract Boundary

## Status

Accepted

## Context

Loop 1 needs to convert validated reference polygons into a raster label representation that aligns exactly with the image grid.

The input reference data contains multiple supervision roles:

- positive landslide references
- reviewed negative references
- hard-negative references
- unlabeled areas
- nodata areas

Not all of these concepts should enter rasterization in the same way.

Only explicit vector evidence should be accepted as a rasterization source.

Unlabeled areas are defined by the absence of supervision, not by a polygon source.

Nodata areas are defined by invalid or missing raster observations, not by reference polygons.

The label raster must also use the exact raster grid already established for image construction.

Creating a second independent grid for labels would risk spatial misalignment between image and training target.

## Decision

Introduce a dedicated vector-to-label-raster contract boundary.

The input contract consists of:

```text
LabelVectorSource
+
LabelRasterizationRequest
+
approved RasterGridSpec
```

A `LabelVectorSource` contains:

```text
source_id
supervision kind
validated geometries
```

Only the following supervision kinds are valid explicit vector sources:

```text
POSITIVE_REFERENCE
NEGATIVE_REFERENCE
HARD_NEGATIVE_REFERENCE
```

The following supervision kinds are not valid vector-source inputs:

```text
UNLABELED
NODATA
```

The label-rasterization request must:

- contain at least one vector source
- use unique source identifiers
- provide a non-empty output name
- use an exact raster grid with a complete affine transform

The rasterization layer does not create its own spatial grid.

It consumes the exact shared raster grid established earlier for image construction.

## Architectural Boundary

The intended flow is:

```text
Raw Vector Source
→ Vector Validation
→ Validated Geometries
→ LabelVectorSource
→ LabelRasterizationRequest
→ Rasterization
```

The validation responsibilities remain separated.

Existing vector validation is responsible for geometry validity, supported geometry types, empty geometries, and source metadata.

The label-rasterization contract validates only the requirements specific to entering the rasterization boundary.

## Consequences

### Positive consequences

- rasterization accepts only explicit supervision evidence
- unlabeled regions cannot accidentally become negative vector sources
- nodata semantics remain separate from reference annotations
- hard-negative identity is preserved
- label construction is tied to the same exact grid used by the image
- geometry-validation logic is not duplicated
- the rasterization boundary remains region-independent

### Trade-offs

- callers must convert validated vector sources into contract objects before rasterization
- the rasterization package depends on the shared raster-grid contract
- geometry validity is assumed to have been checked by the earlier validation stage
- pixel-membership and overlap behavior are intentionally not defined yet

## Alternatives Considered

### Pass raw GeoDataFrames directly to rasterization

Rejected because it would couple rasterization to file-loading and GeoPandas-specific structures.

The current contract uses Shapely geometries instead.

### Allow unlabeled areas as vector sources

Rejected because unlabeled means supervision is unknown, not that an explicit unlabeled polygon exists.

### Allow the label rasterizer to construct its own grid

Rejected because image and label rasters must share the same exact pixel grid.

### Re-run all geometry validation inside rasterization

Rejected because those responsibilities already belong to the vector-validation layer.

## Evidence

The implementation includes:

```text
LabelVectorSource
LabelRasterizationRequest
validate_label_vector_source
validate_label_rasterization_request
```

Focused tests verify:

- preservation of supervision semantics
- use of the approved grid
- rejection of unlabeled vector sources
- rejection of nodata vector sources
- rejection of empty source collections
- rejection of duplicate source identifiers
- requirement for a non-empty output name
- requirement for an exact raster grid

At the time of this decision:

```text
10 focused vector-to-raster tests pass
275 total tests pass
git diff --check is clean
```

## Deferred Decisions

The following concerns belong to the next increment:

```text
pixel-center vs all-touched behavior
polygon overlap policy
boundary-pixel behavior
geometry precedence
out-of-grid handling
```

These will be defined in the rasterization-policy contract.