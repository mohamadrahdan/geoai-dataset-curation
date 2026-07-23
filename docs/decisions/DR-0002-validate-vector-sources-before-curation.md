# DR-0002: Validate Vector Sources Before Dataset Curation

## Status

Accepted

## Context

The dataset-curation workflow depends on geospatial vector sources such as:

- area-of-interest boundaries
- landslide reference polygons
- non-landslide reference polygons
- pseudo-landslide polygons

These sources may contain structural or spatial problems that can affect later processing steps.

Examples include:

- missing geometries
- empty geometries
- unsupported geometry types
- invalid polygon topology
- empty vector sources
- missing coordinate reference systems

Allowing such problems to pass silently into later stages could produce unreliable samples, incorrect rasterization, misleading training labels, or failures during dataset generation.

## Decision

All registered vector sources must pass a validation step before they are used in dataset curation.

The validation workflow must:

1. load the vector source from its registered file path
2. validate source-level metadata
3. validate every geometry
4. collect all detected issues
5. produce a structured validation summary
6. serialize the summary for later reporting

The current validation checks include:

### Source-level checks

- the source must contain at least one feature
- the source must define a coordinate reference system

### Geometry-level checks

- geometry must exist
- geometry must not be empty
- geometry must be a `Polygon` or `MultiPolygon`
- geometry must be topologically valid

A source is considered valid only when no invalid geometries are detected.

Metadata issues are also preserved in the validation report so that downstream workflow decisions can account for them.

## Public Validation API

The validation package exposes(stellt bereit) the following public capabilities:

```python
from geoai_dataset_curation.validation import (
    load_vector_file,
    validate_geometry,
    validate_source,
    validate_source_metadata,
    validate_vector_file,
    validation_summary_to_dict,
)
```

The main end-to-end entry point is:

```python
validate_vector_file(
    source_id=source_id,
    path=source_path,
)
```

This function loads(lädt) the vector source, runs(führt aus) geometry and metadata checks, and returns(gibt zurück) a structured `ValidationSummary`.

## Consequences

### Positive consequences

- invalid source data is detected before dataset generation
- validation behavior is reproducible and testable
- geometry and metadata problems are reported consistently
- later curation stages can depend on a stable validation contract
- validation logic remains independent from dataset-generation logic

### Trade-offs

- every source must go through an additional preprocessing step
- some source files may require manual repair or exclusion
- format-specific behavior, such as automatic CRS interpretation for GeoJSON, must be considered during validation and testing

## Implementation Evidence

The implementation includes:

- validation contracts
- geometry-level checks
- source-level validation summaries
- report serialization
- real vector-file loading with GeoPandas
- metadata validation
- an end-to-end validation pipeline
- unit and integration tests

At the time of this decision, the complete test suite passes with:

```text
22 passed
```

## Future Extensions

Later loops may extend(erweitern) the validation workflow with:

- expected CRS enforcement
- spatial extent checks
- duplicate geometry detection
- overlap analysis
- geometry repair policies
- minimum polygon-area thresholds
- attribute-schema validation
- source-specific validation profiles