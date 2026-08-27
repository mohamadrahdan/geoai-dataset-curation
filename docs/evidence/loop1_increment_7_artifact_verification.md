# Loop 1 — Increment 7: Artifact Retrieval and Verification

## Status

Completed.

## Objective

Verify that a raster artifact exported through the Earth Engine workflow
can be retrieved, opened locally, inspected, and checked against the
approved raster grid before it is accepted for downstream dataset
construction.

## Implemented workflow

Remote raster artifact
→ retrieval
→ local GeoTIFF
→ raster inspection
→ approved-grid verification
→ verified raster artifact

Pixel-alignment verification was also introduced as a separate geometric
quality gate for future image-mask pairing.

## Verification evidence

### Automated tests

Final full test suite:

- 231 tests passed.

The Increment 7 tests cover:

- artifact retrieval contracts;
- Google Drive artifact retrieval;
- GeoTIFF metadata inspection;
- exact approved-grid verification;
- half-pixel alignment mismatch detection;
- CRS mismatch detection;
- integrated retrieval and verification;
- rejection of retrieved artifacts with grid mismatch.

### Live Earth Engine connectivity

Earth Engine initialization succeeded.

A real Earth Engine server request succeeded.

A Sentinel-2 catalog request succeeded.

### Live Earth Engine export

A real Earth Engine export task completed successfully.

Export destination:

- Google Drive folder: `geoai-dataset-curation-smoke`
- file prefix: `tiny_live_export_smoke`

### Live artifact retrieval

The exported GeoTIFF was retrieved from Google Drive through the
Google Drive API.

Observed local artifact:

- file: `tiny_live_export_smoke.tif`
- size: 132380 bytes

### Live GeoTIFF inspection

Observed metadata:

- driver: GTiff
- CRS: EPSG:32639
- width: 97
- height: 112
- band count: 4
- dtype: float64
- pixel size: 10 m × 10 m
- affine origin: 547020, 3374300

Observed affine transform:

`[10, 0, 547020, 0, -10, 3374300]`

### Live approved-grid verification

The retrieved Earth Engine artifact matched the expected grid for:

- CRS;
- width;
- height;
- affine transform.

Result:

`Approved grid match: True`

### Live integrated verification

The production integration path successfully executed:

Google Drive
→ GoogleDriveArtifactRetriever
→ RetrievedRasterArtifact
→ raster inspection
→ approved-grid verification
→ VerifiedRasterArtifact

Result:

`PASS: Live artifact integration succeeded.`

## Architectural decisions

### Retrieval is separated from verification

Remote transport concerns are kept separate from raster inspection and
geometric validation.

This allows the verification workflow to remain independent of Google
Drive and supports future retrieval implementations.

### Approved-grid verification is explicit

A successfully downloaded GeoTIFF is not automatically considered a
valid dataset artifact.

The artifact must satisfy the approved raster-grid contract.

### Pixel alignment is a geometric contract

Raster alignment is based on:

- CRS;
- dimensions;
- affine transform.

Band count and dtype are intentionally excluded because an image and its
mask can be geometrically aligned while having different band counts and
data types.

### Half-pixel shifts are rejected

Matching CRS, dimensions, and nominal resolution are not sufficient.

A shifted affine transform causes alignment verification to fail.

## Boundaries of the evidence

The live checks prove that:

- Earth Engine connectivity works in the current environment;
- a real Earth Engine export can complete;
- the exported artifact can be retrieved from Google Drive;
- the GeoTIFF can be opened locally;
- its raster metadata can be inspected;
- the retrieved artifact can be checked against an expected grid;
- the integrated Drive-to-verified-artifact workflow works.

The current live integration script does not start a fresh Earth Engine
export on every execution.

The current pixel-alignment tests establish the alignment contract, but
live image-mask alignment will require a real rasterized mask in a later
dataset-construction step.

## Remaining observations

The live Earth Engine artifact currently contains four `float64` bands.

This is recorded as an observation rather than treated as an error in
Increment 7. The required dataset dtype and any explicit casting policy
should be decided at the appropriate downstream dataset-construction
stage.

## Closure

- Code works: yes
- Tests pass: yes
- Artifact exists: yes
- Architectural decisions documented: yes
- Measurable evidence recorded: yes

Increment 7 is closed.