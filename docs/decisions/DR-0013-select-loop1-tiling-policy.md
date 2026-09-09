# DR-0013: Select the Loop 1 Tiling Policy

## Status

Accepted

## Context

Loop 1 has a real Sentinel-2 image and a real label raster on the same exact grid.

The shared raster grid is:

```text
CRS: EPSG:32639
width: 5712 pixels
height: 5493 pixels
pixel size: 10 metres
```

The label raster contains:

```text
positive pixels: 17,933
negative pixels: 64,388
ignore pixels: 31,293,695
```

Before candidate tiles can be catalogued, Loop 1 needs one explicit tiling policy.

The decision must define:

```text
tile width
tile height
horizontal stride
vertical stride
overlap
edge policy
```

The policy must balance:

- positive-feature containment
- useful spatial context
- positive-label concentration
- complete raster coverage
- computational expansion
- duplicate source observations
- deterministic window identity
- compatibility with later sampling

The decision cannot be based only on a conventional tile size.

It must be supported by measurements from the real image grid, real label raster, and real positive-reference geometries.

## Candidates Evaluated

The following square tile sizes were evaluated:

```text
128 × 128 pixels
256 × 256 pixels
512 × 512 pixels
```

At the approved 10-metre resolution, their ground footprints are:

```text
128 pixels -> 1,280 × 1,280 metres
256 pixels -> 2,560 × 2,560 metres
512 pixels -> 5,120 × 5,120 metres
```

The following overlap levels were evaluated:

```text
0%
25%
50%
```

The following edge policies were evaluated:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

## Decision

Loop 1 uses:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 64 pixels
overlap percentage: 25%
edge policy: SHIFT_TO_FIT
ground footprint: 2,560 × 2,560 metres
```

The selected policy is represented by:

```text
LOOP1_TILING_LAYOUT
```

## Tile Size Decision

A tile size of 256 pixels was selected because it provides a useful balance between context and label concentration.

The real positive-reference inventory contains:

```text
57 positive features
```

The measured positive-feature maximum-span distribution is:

```text
minimum: 39.66 metres
median: 188.44 metres
p90: 420.01 metres
p95: 514.28 metres
maximum: 780.20 metres
```

Every positive feature is smaller than the selected 2,560-metre tile footprint.

Actual containment analysis for the selected layout measured:

```text
57 / 57 features contained with no context margin
57 / 57 features contained with a 160-metre context margin
50 / 57 features contained with a 320-metre context margin
```

The 128-pixel candidate produced less reliable contextual containment:

```text
45 / 57 features contained with a 160-metre context margin
20 / 57 features contained with a 320-metre context margin
```

The 512-pixel candidate provided more context, but diluted the positive signal across much larger tile areas.

For the 512-pixel candidates:

```text
positive tiles with at least 5% positive coverage: 0
```

The 256-pixel tile therefore preserves meaningful context without the strongest label dilution of the 512-pixel candidate.

## Stride and Overlap Decision

Loop 1 uses a stride of 192 pixels.

For a 256-pixel tile:

```text
overlap = tile size - stride
overlap = 256 - 192
overlap = 64 pixels
```

Therefore:

```text
overlap percentage = 25%
```

The selected overlap ensures complete containment of all 57 positive features without requiring the substantially higher duplication of 50% overlap.

Measured results for the selected layout are:

```text
tile count: 870
positive observation multiplier: 1.479
total read expansion: 1.817x
```

The comparable 50% overlap candidate produced:

```text
tile count: 1,848
positive observation multiplier: 4.000
total read expansion: 3.860x
```

The additional 50% overlap guarantees more large-margin context, but more than doubles the tile count and substantially increases repeated observations.

That additional cost is not justified for the Loop 1 baseline.

## Edge Policy Decision

Loop 1 uses:

```text
SHIFT_TO_FIT
```

This policy:

- preserves complete raster coverage
- produces only full-size tile outputs
- introduces no artificial padding
- preserves deterministic tile dimensions
- shifts the final window in each direction to align with the raster boundary

Measured selected-layout geometry is:

```text
tile count: 870
full tiles: 870
partial tiles: 0
source coverage: 100%
uncovered source pixels: 0
padded output pixels: 0
```

The shifted boundary windows repeat some source pixels.

For the selected layout:

```text
repeated source observations: 25,640,304 pixels
total read expansion: 1.817x
```

This duplication is explicit and measurable.

## Label-Aware Evidence

The selected layout produced:

```text
total tiles: 870
supervised tiles: 50
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
```

Positive-tile concentration was:

```text
positive tiles with at least 1% positive coverage: 11
positive tiles with at least 5% positive coverage: 2
```

Supervision coverage was:

```text
positive-pixel coverage: 100%
negative-pixel coverage: 100%
```

The high number of all-ignore tiles is expected because the real reference inventory supervises only a small portion of the full raster.

These tiles are candidate windows only.

Their inclusion in the training dataset will be decided during sampling and pair generation.

## Consequences

### Positive Consequences

- the Loop 1 layout is explicit and versionable
- tile generation is deterministic
- tile identities remain stable
- all source pixels remain covered
- all current supervised pixels remain covered
- all positive features can be fully contained
- every positive feature can retain at least 160 metres of context
- output tiles have uniform dimensions
- artificial edge padding is avoided
- computational expansion remains lower than the 50% overlap alternative
- later sampling can operate on a stable candidate window population

### Trade-offs

- shifted edge windows repeat source pixels
- 25% overlap does not guarantee a 320-metre margin for all positive features
- only 50 of 870 candidate tiles contain current supervision
- positive references may appear in more than one candidate tile
- spatial duplication must be considered during sampling and splitting
- the selected policy is specific to the Loop 1 evidence and may change in a future dataset version

## Alternatives Considered

### 128 Pixels with 25% Overlap

Not selected.

It generated:

```text
3,420 tiles
45 / 57 features contained with a 160-metre context margin
20 / 57 features contained with a 320-metre context margin
```

It provides higher local label concentration, but weaker contextual containment and a much larger candidate population.

### 256 Pixels with No Overlap

Not selected.

It generated only 506 tiles, but actual positive-feature containment was:

```text
38 / 57 features with no context margin
17 / 57 features with a 160-metre context margin
10 / 57 features with a 320-metre context margin
```

This is insufficient for reliable positive-feature containment.

### 256 Pixels with 50% Overlap

Not selected for the Loop 1 baseline.

It contained all positive features at every evaluated context margin, but produced:

```text
1,848 tiles
4.000 positive observation multiplier
3.860x total read expansion
```

The additional duplication is not justified by the current Loop 1 objective.

### 512 Pixels with 25% Overlap

Not selected.

It provided strong contextual containment with only 210 tiles, but positive supervision was strongly diluted.

Measured label evidence included:

```text
positive tiles: 8
positive tiles with at least 5% positive coverage: 0
```

### DROP_PARTIAL

Not selected.

This policy can leave source pixels uncovered and would discard edge context.

Although no current supervised pixels were lost in the measured candidates, the policy would make coverage dependent on the present label distribution and could discard future supervision near raster edges.

### PAD_PARTIAL

Not selected.

This policy covers the complete raster but introduces artificial output pixels.

For the selected size and stride candidate, padding would add:

```text
1,883,440 pixels
```

Loop 1 does not need artificial padded context when full-size shifted windows can provide complete coverage.

## Architectural Boundary

This decision defines the approved candidate-window layout.

The current flow is:

```text
exact shared raster grid
+
selected tiling policy
↓
validated tiling request
↓
deterministic tile-window generation
↓
stable tile-window identities
↓
candidate tile analysis
```

This decision does not:

- select the final training subset
- balance positive and negative samples
- distinguish ordinary negatives from hard negatives spatially
- write physical image-label training pairs
- assign dataset splits
- create the final dataset manifest

Those responsibilities belong to later phases.

In particular:

```text
L1-7 -> deterministic candidate tile population
L1-8 -> sampling and image-label pair generation
L1-10 -> spatial split assignment
```

## Implementation Evidence

The implementation includes:

```text
LOOP1_TILING_LAYOUT
analyze_tile_layout
analyze_label_tiles
generate_tile_windows
validate_tile_layout
validate_tile_window
```

Real-data analysis scripts include:

```text
scripts/check_real_tiling_layout_geometry.py
scripts/check_real_tile_label_analysis.py
scripts/check_real_positive_reference_scale.py
scripts/check_real_positive_tile_containment.py
```

Automated tests include:

```text
tests/test_tile_layout_analysis.py
tests/test_tile_label_analysis.py
tests/test_loop1_tiling_policy.py
```

At the time of this decision:

```text
52 focused tiling tests pass
375 total tests pass
git diff --check is clean
```

## Decision Summary

The approved Loop 1 tiling policy is:

```text
256 × 256 pixels
192-pixel stride
25% overlap
SHIFT_TO_FIT edge handling
```

This policy provides complete raster coverage, complete positive-feature containment, useful spatial context, deterministic full-size windows, and a controlled computational expansion suitable for the Loop 1 baseline.