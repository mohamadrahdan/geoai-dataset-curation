# Phase L1-5B — Real Image Construction

## Status

Completed.

## Objective

Turn the previously defined image-construction contracts into a real, traceable Sentinel-2 production-style workflow.

The phase was intended to prove that a real study-area input can move through Earth Engine scene discovery, cloud-masked composite construction, deterministic exact-grid export, artifact retrieval, raster verification, and persistent manifest generation without bypassing the internal project contracts.

## Implemented Work

L1-5B introduced and verified the runtime infrastructure required for real Sentinel-2 image construction.

The completed work includes:

- deterministic exact shared raster-grid contracts;
- affine-transform-based grid identity;
- Earth Engine provider and service boundaries;
- explicit Earth Engine runtime and authentication boundaries;
- real Sentinel-2 scene queries;
- SCL-based cloud masking;
- median composite construction;
- exact-grid Earth Engine export;
- export-task lifecycle normalization and polling;
- Google Drive artifact retrieval;
- Rasterio artifact inspection;
- exact raster-grid verification;
- real-image manifest contracts;
- end-to-end orchestration;
- real study-area runtime wiring;
- live production-style execution on the Komeh study area;
- measurable execution evidence and decision closure.

The reusable implementation remains region-independent.

Study-area-specific names, paths, task IDs, and generated raster artifacts are runtime data rather than reusable code contracts.

## Practical Verification

The phase was verified at several levels.

### Automated tests

The final automated test suite completed successfully:

```text
256 passed
```

### Earth Engine connectivity

Live Earth Engine initialization and server communication were verified using the configured Cloud Project.

### Real Sentinel-2 query

The 2024 engineering query for the real study area returned:

```text
176 Sentinel-2 scenes
```

Query configuration:

- collection: `COPERNICUS/S2_SR_HARMONIZED`
- date range: `2024-01-01` to `2024-12-31`
- maximum scene cloud cover: `20%`
- output bands: `B2`, `B3`, `B4`, `B8`

### Real composite construction

The production-style composite used:

- the exact returned scene IDs;
- `B2`, `B3`, `B4`, `B8`;
- the Sentinel-2 `SCL` band for cloud masking;
- excluded SCL classes `1`, `3`, `8`, `9`, `10`, and `11`;
- median temporal aggregation.

### Exact raster grid

The real study area produced the deterministic grid:

```text
CRS: EPSG:32639
Width: 5712
Height: 5493
Pixel size: 10 m
Pixel count: 31,376,016
```

Affine transform:

```text
(10.0, 0.0, 533040.0, 0.0, -10.0, 3451350.0)
```

Grid ID:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

### Real Earth Engine export

A real production-style Earth Engine export completed successfully.

Task ID:

```text
4FIGM5JCUMT7KVSLNSQXWF62
```

Observed lifecycle:

```text
ready
→ running
→ completed
```

Remote artifact:

```text
drive://geoai-dataset-curation-loop1/komeh_sentinel2_2024_median.tif
```

### Real artifact retrieval and inspection

The exported GeoTIFF was retrieved from Google Drive and inspected locally.

Observed metadata:

```text
Driver: GTiff
CRS: EPSG:32639
Width: 5712
Height: 5493
Band count: 4
Dtypes: float64 × 4
File size: 327,525,721 bytes
```

### Exact-grid verification

The retrieved raster matched the approved spatial contract for:

```text
CRS: True
Width: True
Height: True
Affine transform: True
Overall match: True
```

### Real-image manifest

A complete real-image manifest was generated and successfully serialized.

The manifest records:

- artifact identity;
- real artifact metadata;
- exact scene provenance;
- collection and band order;
- cloud-mask policy;
- aggregation method;
- deterministic grid identity;
- Earth Engine task identity;
- export destination;
- remote artifact URI;
- local retrieved path.

## Artifacts

### Runtime artifacts

The live execution produced:

```text
komeh_sentinel2_2024_median.tif
komeh_sentinel2_2024_median.manifest.json
```

These large or runtime-specific artifacts remain outside normal Git history.

### Repository evidence

The repository contains documented evidence for:

- live artifact retrieval and verification;
- real-image manifest construction;
- Increment 9 end-to-end execution;
- Increment 9 decision closure.

## Decisions

The phase reused and validated the established architecture rather than introducing provider-specific Earth Engine logic throughout the pipeline.

Important decisions include:

- Earth Engine is accessed through an internal provider boundary;
- authentication and SDK initialization remain runtime concerns;
- exact raster identity includes CRS, dimensions, pixel size, and affine transform;
- exact-grid export uses an explicit spatial contract;
- a successfully downloaded raster is not automatically accepted;
- retrieved artifacts must be verified against the approved grid;
- manifest provenance must describe the actual composite inputs;
- cross-component manifest consistency is validated before serialization;
- large research artifacts and private source data remain outside Git history.

Increment 9 introduced no additional durable architecture decision requiring a new ADR.

## Measurable Evidence

Final phase evidence includes:

- `256` passing automated tests;
- `176` real Sentinel-2 scene references;
- `4` output spectral bands;
- `31,376,016` raster pixels;
- `5712 × 5493` raster dimensions;
- `10 m` exact resolution;
- `327,525,721 bytes` retrieved GeoTIFF size;
- successful Earth Engine export;
- successful Google Drive retrieval;
- successful Rasterio inspection;
- exact CRS verification;
- exact width verification;
- exact height verification;
- exact affine-transform verification;
- deterministic grid identity;
- successful real-image manifest validation;
- successful JSON-compatible manifest serialization;
- clean `git diff --check`.

## Limitations

L1-5B establishes a real and verified image-construction engineering path, but it does not finalize every scientific image-selection decision.

The following remain intentionally open:

- final multi-year temporal policy;
- whether annual, seasonal, or other compositing strategies are preferable;
- AOI-level pixel-quality metrics;
- final raster storage and model-input dtype;
- possible inclusion of Sentinel-2 SWIR or red-edge bands;
- final scientific comparison of alternative band combinations;
- live image-mask alignment.

The 2024 composite is therefore a verified Loop 1 engineering artifact, not yet a claim that the 2024 temporal strategy is scientifically optimal.

## Completion Checklist

- [x] Code and workflow work
- [x] Automated tests pass
- [x] Real practical execution succeeds
- [x] Real raster artifact exists
- [x] Real manifest exists
- [x] Exact-grid verification succeeds
- [x] Important architectural decisions are documented
- [x] Scientific limitations are explicitly documented
- [x] Measurable evidence exists
- [x] Private source data remains outside Git
- [x] Large generated artifacts remain outside normal Git history

## Closure

L1-5B is complete.

The phase moved image construction from a tested contract boundary to a real end-to-end geospatial data workflow:

```text
Private study-area geometry
→ Sentinel-2 discovery
→ cloud-masked composite
→ deterministic exact grid
→ Earth Engine export
→ Google Drive artifact
→ local retrieval
→ Rasterio inspection
→ exact-grid verification
→ persistent provenance manifest
```

The resulting raster can now serve as the image-side spatial reference for downstream label construction.

## Next Phase

The next immediate phase is:

```text
L1-6A — Label Rasterization Contracts
```

The next objective is to define how validated reference polygons become raster labels on exactly the same approved spatial grid without yet mixing label semantics, rasterization policy, and downstream tiling responsibilities.