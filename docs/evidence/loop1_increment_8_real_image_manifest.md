# Loop 1 — Increment 8: Real Image Manifest

## Status

Completed.

## Objective

Create a persistent, validated, and serializable manifest for one real-image artifact so that the image remains traceable across scene selection, composite construction, raster-grid definition, export, retrieval, and downstream dataset construction.

## Implemented manifest structure

The real-image manifest contains:

### Identity

- schema version
- source ID
- output name
- artifact URI

### Artifact metadata

- file size
- raster driver
- width
- height
- band count
- raster data types

### Scene and composite provenance

- exact source scene IDs
- acquisition dates
- scene cloud-cover metadata
- Sentinel-2 collection
- ordered composite bands
- aggregation method
- cloud-mask band
- excluded SCL classes

### Exact grid metadata

- deterministic grid ID
- CRS
- width
- height
- pixel size
- affine transform

### Export and retrieval traceability

- Earth Engine task ID
- export destination
- destination folder
- remote artifact URI
- local retrieved path

## Validation rules

A complete real-image manifest is rejected when its components describe inconsistent states.

The implemented consistency checks include:

- supported schema version;
- non-empty identity fields;
- required artifact metadata;
- required provenance;
- required exact-grid metadata;
- required export trace;
- artifact URI must match the export/retrieval remote URI;
- artifact width must match approved-grid width;
- artifact height must match approved-grid height;
- artifact band count must match the number of composite bands.

The integration assembly also requires the inspected raster path to match the retrieved raster path.

## Serialization

A valid manifest can be converted to a JSON-compatible representation.

Serialization normalizes:

- Python dates to ISO date strings;
- paths to strings;
- tuples to lists;
- nested domain contracts to dictionaries.

Incomplete or inconsistent manifests are not serialized.

## Integration evidence

The real-image manifest integration test executes the following deterministic path:

Physical GeoTIFF
→ Rasterio inspection
→ artifact metadata extraction
→ scene/composite provenance
→ exact-grid metadata
→ export/retrieval trace
→ complete manifest assembly
→ cross-component validation
→ JSON-compatible serialization

The integration test also verifies that a manifest cannot be assembled when the inspected raster and retrieved raster refer to different local paths.

## Automated test evidence

At Increment 8 closure:

- full automated test suite: 249 tests passed;
- real-image manifest integration tests: 2 tests passed;
- `git diff --check`: clean.

## Architectural decisions

### A separate real-image manifest contract was introduced

The existing `ImageConstructionResult` remains a lightweight construction summary.

The new real-image manifest is a persistent traceability record and therefore carries richer metadata and provenance.

This avoids breaking the existing image-construction contract.

### Manifest data is assembled incrementally

Artifact metadata, provenance, grid metadata, and export traceability are represented as separate nested contracts.

This keeps each concern explicit and testable.

### Existing contracts are reused

Scene preparation, Earth Engine composite requests, raster-grid contracts, raster inspection, export requests, and retrieved-artifact contracts are reused rather than duplicated.

### Provenance must describe actual inputs

Prepared scene IDs must exactly match the scene IDs used for composite construction.

A manifest must not claim provenance for scenes that were not actually used.

### Exact-grid metadata records the approved contract

The manifest stores the approved raster-grid identity.

Actual raster-versus-grid correctness remains the responsibility of the verification layer implemented in Increment 7.

### Serialization requires consistency

The manifest is not treated as a passive metadata container.

Cross-component consistency is validated before serialization.

## Evidence boundaries

Increment 8 proves that the system can:

- represent one complete real-image manifest;
- preserve artifact metadata;
- preserve scene and composite provenance;
- preserve exact-grid identity;
- preserve export and retrieval traceability;
- reject internally inconsistent manifests;
- assemble the components through one integration boundary;
- serialize the result to a JSON-compatible payload.

Increment 8 does not yet prove that a fresh live Earth Engine execution produces a complete truthful real-image manifest in one run.

The earlier live Earth Engine smoke artifact was suitable for connectivity, export, retrieval, and raster verification, but it did not persist the exact production scene provenance and cloud-mask processing needed by the new manifest contract.

That live production-style manifest path belongs to Increment 9.

## Loop 1 scope boundary

No additional manifest features are required for Loop 1 at this stage.

The following are intentionally deferred unless they become necessary later:

- content checksums;
- retry history;
- task polling history;
- quota metadata;
- detailed timestamps;
- storage-provider abstraction beyond current needs;
- manifest schema registry;
- migration framework.

## Closure

- Code works: yes
- Tests pass: yes
- Integration test exists: yes
- Manifest is serializable: yes
- Cross-component consistency is validated: yes
- Architectural decisions documented: yes
- Evidence measurable: yes

Increment 8 is closed.