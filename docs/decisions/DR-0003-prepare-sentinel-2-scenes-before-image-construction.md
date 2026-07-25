# DR-0003: Prepare Sentinel-2 Scenes Before Image Construction

## Status

Accepted

## Context

The dataset-curation workflow requires reproducible Sentinel-2 inputs before image construction can begin.

A simple list of available scenes is not sufficient because different scenes may vary in:

- acquisition date
- cloud cover
- collection
- available spectral bands
- suitability for the study area and dataset workflow

Without an explicit preparation step, scene selection could become inconsistent, difficult to reproduce, and dependent on manual decisions.

The workflow therefore needs a clear contract for:

- defining scene-selection criteria
- validating those criteria
- representing candidate scenes
- selecting matching scenes
- reporting accepted and rejected candidates
- serializing the final preparation result

## Decision

Sentinel-2 scenes must pass through a dedicated scene-preparation workflow before they are used for image construction.

The workflow must:

1. define a scene-selection request
2. validate the request before processing
3. evaluate candidate scenes against all selection criteria
4. produce a structured preparation result
5. serialize the result as a reproducible manifest

## Scene-Selection Criteria

The current request contract includes:

- source identifier
- start date
- end date
- Sentinel-2 collection
- required bands
- maximum cloud-cover threshold

A request is rejected when:

- the start date is later than the end date
- the source identifier is empty
- the collection is empty
- no required bands are defined
- required bands contain duplicates
- cloud cover is outside the range from 0 to 100

## Candidate Selection

A candidate scene is selected only when:

- its acquisition date falls within the requested date range
- its collection matches the requested collection
- its cloud cover is below or equal to the configured threshold
- it contains all required bands

Candidates that do not satisfy all criteria are rejected from the prepared result.

## Preparation Result

The workflow returns a structured `ScenePreparationResult` containing:

- source identifier
- total candidate count
- selected scene count
- rejected scene count
- selected scene records
- whether at least one scene was selected

## Public Scene-Preparation API

The scene-preparation package exposes the following public capabilities:

```python
from geoai_dataset_curation.scene_preparation import (
    SceneCandidate,
    ScenePreparationResult,
    SceneSelectionRequest,
    prepare_scenes,
    scene_preparation_result_to_dict,
    select_scene_candidates,
    validate_scene_selection_request,
)
```

The main end-to-end entry point is:

```python
prepare_scenes(
    request=request,
    candidates=candidates,
)
```

This function validates the request, filters the candidates, and returns a structured scene-preparation result.

## Manifest Serialization

The preparation result can be converted into a serializable dictionary.

The manifest contains:

- source identifier
- candidate, selected, and rejected counts
- selected scene identifiers
- acquisition dates
- cloud-cover values
- collection names
- available bands

This manifest is intended to support reproducibility, later image construction, and traceability of scene-selection decisions.

## Consequences

### Positive consequences

- scene selection becomes explicit and reproducible
- invalid requests are rejected before candidate evaluation
- selected and rejected counts are measurable
- downstream image construction receives controlled inputs
- scene-selection logic remains independent from image-generation logic
- the manifest can serve as an artifact for later dataset versions

### Trade-offs

- candidate metadata must be available before preparation
- the current implementation relies on preconstructed scene candidates
- cloud-cover filtering is based on scene-level metadata rather than pixel-level cloud masking
- source-to-scene spatial overlap is not yet evaluated
- temporal ranking and best-scene selection are not yet implemented

## Implementation Evidence

The implementation includes:

- scene-selection request contracts
- scene-candidate contracts
- request-validation rules
- candidate-selection logic
- preparation-result contracts
- an end-to-end preparation pipeline
- manifest serialization
- unit and integration tests

At the time of this decision, the complete test suite passes with:

```text
41 passed
```

## Future Extensions

Later phases or loops may extend the workflow with:

- scene retrieval from Google Earth Engine or another catalog
- AOI intersection checks
- pixel-level cloud and shadow masking
- scene ranking
- seasonal constraints
- temporal compositing rules
- duplicate-scene detection
- spatial coverage thresholds
- provenance and catalog metadata
- persistent JSON manifest files