# DR-0004: Define Image Construction as a Controlled Contract Boundary

## Status

Accepted

## Context

The dataset-curation workflow needs a controlled transition from selected Sentinel-2 scenes to raster artifacts that can later be used for dataset construction.

Scene preparation determines which scenes are eligible, but it does not define how the resulting raster output should be described, validated, or tracked.

Without an explicit image-construction boundary, later processing could depend on implicit assumptions about:

- source identity
- selected scene identifiers
- band order
- raster dimensions
- pixel size
- coordinate reference system
- artifact naming
- artifact location

These assumptions would make the workflow harder to validate, reproduce, test, and extend.

## Decision

Image construction must be represented as a dedicated contract-driven workflow.

The workflow must:

1. define an explicit image-construction request
2. validate request-level fields
3. validate the target raster-grid specification
4. produce a structured construction result
5. require an explicit artifact URI
6. serialize the result into a reproducible manifest

## Image-Construction Request

The request contract includes:

- source identifier
- selected scene identifiers
- ordered band identifiers
- target raster-grid specification
- output name

The request is rejected when:

- the source identifier is empty
- no scene identifiers are provided
- scene identifiers contain duplicates
- no bands are provided
- bands contain duplicates
- the output name is empty

## Raster-Grid Specification

The target grid is represented by `RasterGridSpec`.

It contains:

- coordinate reference system
- raster width
- raster height
- horizontal pixel size
- vertical pixel size

The grid is rejected when:

- the CRS is empty
- width is not greater than zero
- height is not greater than zero
- horizontal pixel size is not greater than zero
- vertical pixel size is not greater than zero

## Construction Result

The workflow returns an `ImageConstructionResult` containing:

- source identifier
- output name
- scene count
- band count
- target grid
- artifact URI
- whether an artifact is available

The result provides a structured summary of one image-construction run.

## Public Image-Construction API

The package exposes:

```python
from geoai_dataset_curation.image_construction import (
    ImageConstructionRequest,
    ImageConstructionResult,
    RasterGridSpec,
    construct_image,
    image_construction_result_to_dict,
    validate_image_construction_request,
    validate_raster_grid_spec,
)
```

The main orchestration entry point is:

```python
construct_image(
    request=request,
    artifact_uri=artifact_uri,
)
```

This function validates the request and returns a structured construction result.

## Manifest Serialization

The construction result can be converted into a serializable dictionary.

The manifest contains:

- source identifier
- output name
- scene count
- band count
- artifact URI
- artifact availability
- CRS
- raster width
- raster height
- horizontal pixel size
- vertical pixel size

This manifest establishes a traceable boundary between image construction and later dataset-building steps.

## Architectural Boundary

The current implementation defines the contract and orchestration boundary for image construction.

It does not yet perform:

- raster file reading
- Sentinel-2 retrieval
- AOI clipping
- band stacking
- resampling
- reprojection
- cloud masking
- temporal compositing
- GeoTIFF writing

Those capabilities belong to later implementation steps or provider-specific adapters.

The current phase intentionally separates workflow control from raster-processing execution.

## Consequences

### Positive consequences

- image-construction inputs become explicit
- invalid grid definitions are rejected early
- band and scene selection remain traceable
- downstream steps receive a structured raster description
- artifact metadata can be persisted independently
- raster-processing implementations can be added behind a stable contract
- the core workflow remains independent from a specific raster library or provider

### Trade-offs

- the current pipeline requires an artifact URI supplied by the caller
- artifact existence is not verified on disk
- no raster data is created by the current implementation
- CRS syntax is not yet parsed or validated semantically
- band compatibility and spatial alignment are not yet checked against real raster inputs
- scene count and band count are derived from request metadata rather than inspected raster content

## Implementation Evidence

The implementation includes:

- image-construction request contracts
- raster-grid contracts
- request-validation rules
- raster-grid validation
- construction-result contracts
- an orchestration pipeline
- construction-manifest serialization
- focused unit and integration tests

At the time of this decision, the complete test suite passes with:

```text
61 passed
```

## Future Extensions

Later phases or loops may extend the workflow with:

- Rasterio-based raster reading and writing
- real GeoTIFF artifact creation
- AOI clipping
- reprojection
- grid alignment
- band ordering and stacking
- resampling policies
- nodata handling
- cloud and shadow masking
- temporal compositing
- artifact existence and checksum validation
- persistent JSON construction manifests