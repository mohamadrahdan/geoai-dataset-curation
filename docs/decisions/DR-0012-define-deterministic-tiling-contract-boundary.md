# DR-0012: Define a Deterministic Tiling Contract Boundary

## Status

Accepted

## Context

Loop 1 now has a real Sentinel-2 image raster and a real label raster that share the same exact pixel grid.

The verified raster pair uses:

```text
CRS: EPSG:32639
width: 5712
height: 5493
pixel resolution: 10 metres
exact shared affine transform
```

The next workflow stage must divide this shared raster space into candidate tile windows.

Tiling decisions can materially affect:

- spatial context
- boundary coverage
- computational cost
- later class balancing
- later sampling
- reproducibility
- spatial leakage risk

Tile size, stride, overlap, and edge behavior must therefore be explicit rather than hidden inside raster-reading loops.

Tiling must also remain separate from sampling.

Tiling defines which deterministic spatial windows exist.

Sampling later decides which candidate windows enter the dataset.

## Decision

Introduce a dedicated deterministic tiling contract boundary.

The input contract is:

```text
TilingRequest
=
image artifact path
+ label artifact path
+ exact RasterGridSpec
+ verified grid identity
+ TileLayoutSpec
+ output identity
```

The tile-layout contract explicitly records:

```text
tile width
tile height
horizontal stride
vertical stride
edge policy
```

The supported edge-policy candidates are:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

These values represent design alternatives.

This decision does not yet select the final Loop 1 edge policy.

The layout contract rejects nonpositive dimensions and strides.

It also requires:

```text
stride_x <= tile_width
stride_y <= tile_height
```

This prevents unrepresented spatial gaps between candidate windows.

Each generated candidate window is represented by a `TileWindowSpec` containing:

```text
tile identity
row index
column index
row offset
column offset
source read width
source read height
output width
output height
```

Partial windows are allowed only under the padding policy.

A partial-width window must touch the right raster edge.

A partial-height window must touch the bottom raster edge.

Drop and shift-to-fit policies must not produce partial output windows.

## Stable Identity

Tile layouts and tile windows use canonical SHA-256 identities.

The layout identity depends on:

```text
tile dimensions
stride
edge policy
identity schema version
```

The window identity depends on:

```text
grid identity
layout identity
row and column indices
pixel offsets
source read dimensions
identity schema version
```

Therefore, the same exact grid, layout, and window produce the same identity.

A material change to the grid, layout, position, or read dimensions produces a different identity.

The request grid identity must match the identity computed from its exact raster-grid specification.

A stored tile identity must also match the identity computed from its actual window content.

## Architectural Boundary

The intended flow is:

```text
Verified Image Raster
+
Verified Label Raster
+
Exact Shared Grid
↓
TilingRequest
↓
TileLayoutSpec
↓
Deterministic Window Generation
↓
Validated TileWindowSpec Collection
↓
Candidate Tile Catalog
↓
Later Sampling and Pair Generation
```

This boundary defines spatial candidates only.

It does not select training examples.

## Consequences

### Positive Consequences

- tile geometry becomes explicit and testable
- tiling results can be reproduced exactly
- layout changes produce new identities
- raster-edge behavior cannot remain implicit
- spatial gaps are rejected
- invalid or out-of-grid windows are rejected
- image and label tiling remain tied to one shared grid
- candidate generation remains separate from sampling
- later manifests can trace every tile to its grid and layout

### Trade-offs

- tiling requires additional contract and identity metadata
- callers must provide the exact shared grid and its identity
- window generators must construct identities from canonical content
- different layouts intentionally produce incompatible tile identities
- the final Loop 1 layout still requires empirical evaluation

## Alternatives Considered

### Use Filenames as Tile Identities

Rejected because filenames do not prove which grid, layout, or window produced a tile.

### Use Random Identifiers

Rejected because independently repeated tiling runs would produce different identities for the same spatial windows.

### Hide Tile Size and Stride Inside Execution Code

Rejected because scientific tiling choices would become implicit and difficult to audit.

### Generate Physical Training Pairs During Tiling

Rejected because it would combine deterministic spatial enumeration with sampling and dataset selection.

Physical pair generation belongs to L1-8.

### Allow Stride Larger Than Tile Dimensions

Rejected because it would create spatial gaps that are absent from the candidate catalog.

## Evidence

The implementation includes:

```text
TileEdgePolicy
TileLayoutSpec
TileWindowSpec
TilingRequest
validate_tile_layout
validate_tile_window
validate_tile_window_identity
validate_tiling_request
tile_layout_identity_payload
build_tile_layout_id
tile_window_identity_payload
build_tile_window_id
```

Tests verify:

- valid layout preservation
- rejection of nonpositive tile dimensions
- rejection of nonpositive strides
- rejection of spatial gaps
- rejection of unsupported edge policies
- exact-grid requirements
- request and grid-identity consistency
- valid full windows
- valid padded edge windows
- rejection of negative offsets
- rejection of invalid dimensions
- rejection of out-of-grid windows
- edge-policy compatibility
- stable layout identities
- stable tile-window identities
- identity changes after material input changes

At the time of this decision:

```text
32 focused tiling tests pass
355 total tests pass
git diff --check is clean
```

## Scope Boundary

This decision does not yet:

- choose the final Loop 1 tile size
- choose the final stride
- choose the final overlap
- choose the final edge policy
- generate the complete real window collection
- inspect label coverage per candidate tile
- create physical image and label tiles
- select training samples
- balance positive and negative samples
- assign train, validation, or test splits

Tile-layout selection belongs to L1-7B.

Sampling and physical pair generation belong to L1-8.

Spatial split assignment belongs to L1-10.