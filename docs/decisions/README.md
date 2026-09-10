# Decision Records

This directory contains the architectural and dataset-design decisions made during the development of the GeoAI Dataset Curation pipeline.

Each decision record documents:

- the problem or context
- the selected decision
- the consequences
- the alternatives considered
- the available implementation evidence
- the explicit scope boundary

## Decision index

- [DR-0001: Use a Binary Segmentation Label Contract](DR-0001-use-binary-segmentation-label-contract.md)
- [DR-0002: Validate Vector Sources Before Dataset Curation](DR-0002-validate-vector-sources-before-curation.md)
- [DR-0003: Prepare Sentinel-2 Scenes Before Image Construction](DR-0003-prepare-sentinel-2-scenes-before-image-construction.md)
- [DR-0004: Define Image Construction as a Controlled Contract Boundary](DR-0004-define-image-construction-as-a-controlled-contract-boundary.md)
- [DR-0005: Establish an Exact Shared Raster Grid](DR-0005-establish-an-exact-shared-raster-grid.md)
- [DR-0006: Introduce an Earth Engine Provider Boundary](DR-0006-introduce-an-earth-engine-provider-boundary.md)
- [DR-0007: Keep Earth Engine Authentication Behind a Runtime Boundary](DR-0007-earth-engine-authentication-boundary.md)
- [DR-0008: Separate Supervision Semantics from Training Targets](DR-0008-separate-supervision-semantics-from-training-targets.md)
- [DR-0009: Define the Vector-to-Label-Raster Contract Boundary](DR-0009-define-vector-to-label-raster-contract.md)
- [DR-0010: Define the Loop 1 Label Rasterization Policy](DR-0010-define-loop1-label-rasterization-policy.md)
- [DR-0011: Define the Label Artifact and Verification Contract](DR-0011-define-label-artifact-and-verification-contract.md)
- [DR-0012: Define a Deterministic Tiling Contract Boundary](DR-0012-define-deterministic-tiling-contract-boundary.md)
- [DR-0013: Select the Loop 1 Tiling Policy](DR-0013-select-loop1-tiling-policy.md)
- [DR-0014: Persist the Candidate Tile Catalog Before Sampling](DR-0014-persist-candidate-tile-catalog-before-sampling.md)
