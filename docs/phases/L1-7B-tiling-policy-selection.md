# L1-7B — Tiling Policy Selection

## Objective

The objective of L1-7B was to select one deterministic, evidence-based tiling policy for the Loop 1 dataset.

L1-7A established the tiling contracts, validation rules, and stable tile identity boundary.

L1-7B converts those contracts into:

- deterministic tile-window generation
- measurable candidate-layout analysis
- real label-aware analysis
- positive-reference scale analysis
- actual feature-containment analysis
- one approved Loop 1 tiling policy

The selected layout defines the candidate-window population that will be catalogued before sampling and pair generation.

## Starting Point

L1-7B began with:

```text
a real Sentinel-2 image
a real aligned label raster
an exact shared raster grid
explicit label semantics
validated tiling contracts
stable layout identities
stable tile-window identities
```

Real grid:

```text
CRS: EPSG:32639
width: 5712 pixels
height: 5493 pixels
pixel size: 10 × 10 metres
```

Real supervision:

```text
57 positive-reference features
17,933 positive pixels
64,388 negative pixels
31,293,695 ignore pixels
```

## Completed Increments

### L1-7B.1 — Deterministic Tile-Window Generation

Implemented deterministic window generation for:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

The generator provides:

- deterministic row-major ordering
- explicit source offsets
- explicit read dimensions
- explicit output dimensions
- stable window identities
- edge-policy-aware behavior
- request and window validation

Generated windows are reproducible from:

```text
exact raster grid
+
tile layout
```

No raster pixel data is required to generate the window definitions.

### L1-7B.2 — Candidate Layout Geometry Analysis

Implemented candidate-layout analysis for:

- tile count
- full-tile count
- partial-tile count
- unique source coverage
- uncovered source pixels
- total source reads
- repeated source observations
- padded output pixels
- coverage ratio
- total read expansion

This made the computational and spatial consequences of each candidate measurable.

### L1-7B.3 — Real Candidate Matrix Execution

Executed the candidate matrix against the real Loop 1 raster grid.

Evaluated:

```text
3 tile sizes
3 overlap levels
3 edge policies
27 geometry candidates
```

Tile sizes:

```text
128 × 128 pixels
256 × 256 pixels
512 × 512 pixels
```

Overlap levels:

```text
0%
25%
50%
```

Edge policies:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

The real execution confirmed that:

- partial dropping can leave source pixels uncovered
- padding preserves coverage but creates artificial output pixels
- shifting to fit preserves coverage without artificial padding
- increased overlap substantially increases repeated observations
- larger tiles reduce tile count but dilute local supervision

### L1-7B.4 — Label-Aware Tile Analysis

Implemented analysis of the real label raster for every candidate window population.

Measured:

- supervised tile count
- positive tile count
- negative-only tile count
- all-ignore tile count
- positive-pixel coverage
- negative-pixel coverage
- positive observation multiplier
- positive tiles above 1% coverage
- positive tiles above 5% coverage
- padded ignore pixels

The analysis preserved the semantic rule:

```text
UNLABELED != NEGATIVE
```

Pixels with value 255 remained ignored.

An all-ignore tile was not treated as a negative tile.

Ordinary negative and hard-negative provenance were not reconstructed from the label raster because both use training target zero.

That provenance distinction remains available from the vector sources for later sampling.

### L1-7B.5 — Positive Scale and Containment Analysis

Measured the real positive-reference geometry distribution in:

```text
EPSG:32639
```

Positive feature count:

```text
57
```

Measured maximum span:

```text
minimum: 39.66 metres
median: 188.44 metres
p90: 420.01 metres
p95: 514.28 metres
maximum: 780.20 metres
```

The analysis first verified whether each feature could theoretically fit inside each tile footprint.

It then measured actual containment using:

- real feature geometry
- real raster transform
- deterministic window placement
- multiple context margins

Evaluated context margins:

```text
0 metres
160 metres
320 metres
```

This distinguished theoretical footprint capacity from actual containment under the real tile layout.

### L1-7B.6 — Loop 1 Policy Selection

The approved policy is:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 64 pixels
overlap percentage: 25%
edge policy: SHIFT_TO_FIT
ground footprint: 2,560 × 2,560 metres
```

The policy is implemented as:

```text
LOOP1_TILING_LAYOUT
```

## Selected Policy Evidence

### Geometry

```text
tile count: 870
full tiles: 870
partial tiles: 0
source coverage: 100%
uncovered source pixels: 0
padded output pixels: 0
repeated source observations: 25,640,304 pixels
total read expansion: 1.817x
```

### Labels

```text
supervised tiles: 50
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
positive tiles with at least 1% positive coverage: 11
positive tiles with at least 5% positive coverage: 2
positive-pixel coverage: 100%
negative-pixel coverage: 100%
positive observation multiplier: 1.479
```

### Positive-Feature Containment

```text
no context margin: 57 / 57
160-metre context margin: 57 / 57
320-metre context margin: 50 / 57
```

## Why This Policy Was Selected

The selected policy balances the primary Loop 1 requirements.

It provides:

- complete raster coverage
- complete supervision coverage
- complete positive-feature containment
- at least 160 metres of context for every positive feature
- no artificial padding
- deterministic full-size windows
- lower duplication than the 50% overlap alternative
- stronger label concentration than the 512-pixel alternative
- a manageable candidate population

The selected layout does not optimize one metric in isolation.

It provides the best measured compromise for the Loop 1 baseline.

## Why 50% Overlap Was Not Selected

The 256-pixel candidate with 50% overlap provided complete containment at every evaluated context margin.

However, it produced:

```text
tile count: 1,848
positive observation multiplier: 4.000
total read expansion: 3.860x
```

The selected 25% overlap policy produced:

```text
tile count: 870
positive observation multiplier: 1.479
total read expansion: 1.817x
```

The additional duplication and computational cost of 50% overlap were not justified for the Loop 1 baseline.

## Why 128 Pixels Was Not Selected

The 128-pixel candidate with 25% overlap produced:

```text
3,420 tiles
45 / 57 features with a 160-metre context margin
20 / 57 features with a 320-metre context margin
```

It provides stronger local positive-label concentration but weaker contextual containment and a much larger candidate population.

## Why 512 Pixels Was Not Selected

The 512-pixel candidate with 25% overlap provided strong containment with only 210 tiles.

However, label concentration was reduced:

```text
positive tiles: 8
positive tiles with at least 5% positive coverage: 0
```

This footprint is unnecessarily large for the measured positive-feature scale in Loop 1.

## Final Runtime Flow

The completed L1-7B flow is:

```text
exact shared raster grid
↓
candidate tile layouts
↓
deterministic tile-window generation
↓
stable tile-window identities
↓
geometry analysis
↓
real label-aware analysis
↓
positive-reference scale analysis
↓
actual feature-containment analysis
↓
evidence-based policy selection
↓
LOOP1_TILING_LAYOUT
```

## Implementation

Primary package:

```text
src/geoai_dataset_curation/tiling/
```

Implemented modules:

```text
contracts.py
validation.py
identity.py
window_generation.py
analysis.py
label_analysis.py
policy.py
```

Real-data analysis scripts:

```text
scripts/check_real_tiling_layout_geometry.py
scripts/check_real_tile_label_analysis.py
scripts/check_real_positive_reference_scale.py
scripts/check_real_positive_tile_containment.py
```

Automated tests:

```text
tests/test_tiling_contracts.py
tests/test_tiling_validation.py
tests/test_tile_identity.py
tests/test_tile_window_generation.py
tests/test_tile_layout_analysis.py
tests/test_tile_label_analysis.py
tests/test_loop1_tiling_policy.py
```

## Decision and Evidence Records

Decision record:

```text
docs/decisions/DR-0013-select-loop1-tiling-policy.md
```

Evidence record:

```text
docs/evidence/loop1_increment_15_tiling_policy_analysis.md
```

## Validation Summary

At L1-7B closure:

```text
deterministic window generation: PASS
stable tile identity validation: PASS
candidate geometry analysis: PASS
real label-aware analysis: PASS
positive-reference scale analysis: PASS
actual feature-containment analysis: PASS
selected policy validation: PASS
focused tiling tests: 52 passed
complete test suite: 375 passed
git diff --check: clean
```

## Scope Boundary

L1-7B selects the tiling policy and defines the deterministic candidate-window population.

It does not:

- select the final training subset
- materialize image-label tile pairs
- balance positive and negative samples
- apply hard-negative sampling rules
- assign spatial dataset splits
- publish a final dataset version

The downstream boundary remains:

```text
L1-7  -> deterministic tiling and candidate windows
L1-8  -> sampling and pair generation
L1-10 -> spatial split
L1-11 -> manifest and dataset version
```

## Closure Criteria

```text
Code works: PASS
Tests pass: PASS
Real analysis exists: PASS
Decision documented: PASS
Evidence measurable: PASS
Policy implemented: PASS
Scope boundary preserved: PASS
```

## Closure Decision

L1-7B is complete.

The project now has an explicit, tested, reproducible, and evidence-based Loop 1 tiling policy.

The next L1-7 increment can use this policy to build and verify the persistent candidate tile catalog without performing training-sample selection.