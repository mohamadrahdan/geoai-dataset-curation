# Loop 1 — Increment 9: End-to-End Execution Evidence

## Status

Completed and live-verified.

## Objective

Execute the real Sentinel-2 image-construction workflow from a private study-area input through Earth Engine processing, exact-grid export, artifact retrieval, raster verification, and final manifest generation.

The purpose of this increment was not to introduce another abstraction layer. It was to prove that the previously implemented contracts and components work together on a real study area and produce a traceable raster artifact.

## Real runtime input

The execution used the real Komeh study-area polygon as a private local input.

The runtime study-area contract reported:

- study area ID: `komeh-study-area`
- source ID: `padena_aoi`
- source CRS: `EPSG:4326`
- target raster CRS: `EPSG:32639`
- raster resolution: `10 m`

The private shapefile path was provided through an environment variable and was not committed to the repository.

## Sentinel-2 query

The live Earth Engine query used:

- collection: `COPERNICUS/S2_SR_HARMONIZED`
- start date: `2024-01-01`
- end date: `2024-12-31`
- maximum scene cloud cover: `20%`
- required output bands:
  - `B2`
  - `B3`
  - `B4`
  - `B8`

The real query returned:

- candidate scene count: `176`

These scene references were then used directly to construct the production composite.

## Composite construction

The real composite used:

- exact returned Sentinel-2 scene IDs
- bands: `B2`, `B3`, `B4`, `B8`
- cloud-mask band: `SCL`
- excluded SCL classes:
  - `1`
  - `3`
  - `8`
  - `9`
  - `10`
  - `11`
- temporal aggregation: `median`

The live composite reference was:

`sentinel2-composite:median:176-scenes`

At this stage the Earth Engine image graph was successfully constructed. Actual raster materialization was verified by the later export and retrieval steps.

## Exact raster grid

The real study-area geometry was transformed to `EPSG:32639` and its projected bounds were snapped outward to the 10-meter raster grid.

The approved exact grid was:

- CRS: `EPSG:32639`
- width: `5712`
- height: `5493`
- pixel size x: `10.0`
- pixel size y: `10.0`
- total pixels: `31,376,016`

Raster bounds:

- left: `533040.0`
- bottom: `3396420.0`
- right: `590160.0`
- top: `3451350.0`

Affine transform:

```text
(10.0, 0.0, 533040.0, 0.0, -10.0, 3451350.0)
```

Deterministic grid ID:

```text
sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799
```

## Real Earth Engine export

The production-style composite was exported through the project Earth Engine provider boundary.

The export used:

- destination: Google Drive
- destination folder: `geoai-dataset-curation-loop1`
- output name: `komeh_sentinel2_2024_median`
- exact CRS: `EPSG:32639`
- exact affine transform
- exact export region derived from the approved raster grid

The export task was:

```text
4FIGM5JCUMT7KVSLNSQXWF62
```

Observed task lifecycle:

```text
ready
→ running
→ completed
```

The task reached the normalized terminal state:

```text
completed
```

The completed export produced:

```text
drive://geoai-dataset-curation-loop1/komeh_sentinel2_2024_median.tif
```

## Artifact retrieval

The exported GeoTIFF was retrieved from Google Drive using the existing artifact-retrieval boundary.

Local runtime path:

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

The retrieved artifact existed locally and was successfully opened with Rasterio.

## Real raster metadata

Raster inspection reported:

- driver: `GTiff`
- CRS: `EPSG:32639`
- width: `5712`
- height: `5493`
- band count: `4`
- data types:
  - `float64`
  - `float64`
  - `float64`
  - `float64`
- file size: `327,525,721 bytes`

The actual raster transform was:

```text
(10.0, 0.0, 533040.0, 0.0, -10.0, 3451350.0)
```

## Exact-grid verification

The downloaded raster was compared against the approved raster-grid contract.

Verification results:

- CRS match: `True`
- width match: `True`
- height match: `True`
- affine-transform match: `True`
- overall grid match: `True`

This confirms that the downloaded raster artifact matches the exact spatial contract requested before export.

## Final real-image manifest

A complete real-image manifest was generated from the real execution state.

Manifest path:

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.manifest.json
```

The manifest records:

- schema version
- source ID
- output name
- artifact URI
- actual artifact metadata
- exact source-scene provenance
- Sentinel-2 collection
- ordered output bands
- median aggregation policy
- SCL cloud-mask policy
- deterministic grid ID
- exact CRS and affine transform
- Earth Engine task ID
- export destination
- Drive folder
- remote artifact URI
- local retrieved-artifact path

The generated manifest contained:

- scene count: `176`
- artifact dimensions: `5712 × 5493`
- artifact band count: `4`
- artifact file size: `327,525,721 bytes`
- grid ID: `sha256:d8f4012bcb976699527e0290ea96732d44aa2ba448ccbb58a4b64adcdadea799`
- Earth Engine task ID: `4FIGM5JCUMT7KVSLNSQXWF62`

Manifest validation and JSON serialization both completed successfully.

## Proven runtime path

The live execution verified the following path:

```text
Private Komeh study-area input
→ validated runtime contracts
→ real Sentinel-2 Earth Engine query
→ 176 real scene references
→ SCL cloud masking
→ B2/B3/B4/B8 median composite
→ exact 10-meter raster-grid construction
→ Earth Engine exact-grid export
→ completed cloud task
→ Google Drive GeoTIFF
→ local artifact retrieval
→ Rasterio metadata inspection
→ exact-grid verification
→ validated real-image manifest
```

## Measurable evidence

The final live evidence includes:

- `176` real Sentinel-2 scene records
- `4` output bands
- `31,376,016` raster pixels
- `5712 × 5493` exact raster dimensions
- `10 m` raster resolution
- `327,525,721 bytes` real GeoTIFF artifact
- exact CRS match
- exact dimension match
- exact affine-transform match
- successful Earth Engine export task
- successful Google Drive retrieval
- successful manifest validation
- successful manifest serialization

## Scope boundary

This increment proves the real image-construction path for the current Loop 1 engineering configuration.

It does not yet claim that:

- the 2024 temporal window is the final scientific imagery policy;
- the current four-band baseline is the optimal modeling configuration;
- all future years should be merged into one long-term median;
- `float64` is the final storage or training dtype;
- the current scene-level cloud threshold is sufficient as the final AOI-level quality policy.

Those decisions belong to later scientific refinement and Loop 2 quality work.

The current evidence establishes that the production-style image-construction system works end to end on real data and produces a spatially verified, traceable artifact.