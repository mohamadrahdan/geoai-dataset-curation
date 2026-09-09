# Loop 1 Increment 15 — Tiling Policy Analysis Evidence

## Objective

This evidence record documents the real-data analysis used to select the Loop 1 tiling policy.

The analysis evaluates candidate layouts against:

- the real Sentinel-2 raster grid
- the real label raster
- the real positive-reference geometries
- deterministic edge behavior
- computational expansion
- positive-feature containment
- label concentration

The objective is to select one reproducible candidate-window layout before candidate tile cataloguing and later sampling.

## Real Inputs

### Sentinel-2 Image

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

### Label Raster

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

### Shared Grid

```text
CRS: EPSG:32639
width: 5712 pixels
height: 5493 pixels
pixel size: 10 × 10 metres
```

The image grid identity matches the approved manifest:

```text
True
```

### Label Values

```text
0   = NEGATIVE
1   = POSITIVE
255 = IGNORE
```

Measured label counts:

```text
positive pixels: 17,933
negative pixels: 64,388
ignore pixels: 31,293,695
total pixels: 31,376,016
```

### Positive References

```text
feature count: 57
target CRS: EPSG:32639
```

## Candidate Matrix

The evaluated tile sizes were:

```text
128 × 128 pixels
256 × 256 pixels
512 × 512 pixels
```

The evaluated overlap levels were:

```text
0%
25%
50%
```

The evaluated edge policies were:

```text
DROP_PARTIAL
PAD_PARTIAL
SHIFT_TO_FIT
```

This produced 27 geometry candidates.

## Positive-Reference Scale Evidence

Measured positive-feature statistics:

| Metric | Minimum | P25 | Median | P75 | P90 | P95 | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|
| Area in square metres | 827.52 | 5,762.57 | 11,830.03 | 31,577.12 | 86,911.27 | 104,380.42 | 311,658.60 |
| Width in metres | 33.01 | 104.95 | 157.08 | 264.56 | 330.78 | 397.33 | 780.20 |
| Height in metres | 39.66 | 102.45 | 148.87 | 263.71 | 415.17 | 488.08 | 716.97 |
| Maximum span in metres | 39.66 | 134.94 | 188.44 | 313.88 | 420.01 | 514.28 | 780.20 |
| Equivalent diameter in metres | 32.46 | 85.66 | 122.73 | 200.51 | 332.65 | 364.34 | 629.93 |

All 57 positive features fit within every evaluated tile footprint when footprint size alone is considered:

| Tile size | Ground footprint | Features within footprint |
|---:|---:|---:|
| 128 pixels | 1,280 metres | 57 / 57 |
| 256 pixels | 2,560 metres | 57 / 57 |
| 512 pixels | 5,120 metres | 57 / 57 |

Footprint size alone does not guarantee actual containment because feature placement relative to tile boundaries also matters.

## Actual Positive-Feature Containment

Containment was measured using the real feature geometries and actual deterministic window placement.

### No Context Margin

| Tile size | Overlap | Contained features | Percentage |
|---:|---:|---:|---:|
| 128 | 0% | 34 / 57 | 59.649% |
| 128 | 25% | 54 / 57 | 94.737% |
| 128 | 50% | 57 / 57 | 100.000% |
| 256 | 0% | 38 / 57 | 66.667% |
| 256 | 25% | 57 / 57 | 100.000% |
| 256 | 50% | 57 / 57 | 100.000% |
| 512 | 0% | 46 / 57 | 80.702% |
| 512 | 25% | 57 / 57 | 100.000% |
| 512 | 50% | 57 / 57 | 100.000% |

### 160-Metre Context Margin

| Tile size | Overlap | Contained features | Percentage |
|---:|---:|---:|---:|
| 128 | 0% | 11 / 57 | 19.298% |
| 128 | 25% | 45 / 57 | 78.947% |
| 128 | 50% | 54 / 57 | 94.737% |
| 256 | 0% | 17 / 57 | 29.825% |
| 256 | 25% | 57 / 57 | 100.000% |
| 256 | 50% | 57 / 57 | 100.000% |
| 512 | 0% | 41 / 57 | 71.930% |
| 512 | 25% | 57 / 57 | 100.000% |
| 512 | 50% | 57 / 57 | 100.000% |

### 320-Metre Context Margin

| Tile size | Overlap | Contained features | Percentage |
|---:|---:|---:|---:|
| 128 | 0% | 1 / 57 | 1.754% |
| 128 | 25% | 20 / 57 | 35.088% |
| 128 | 50% | 27 / 57 | 47.368% |
| 256 | 0% | 10 / 57 | 17.544% |
| 256 | 25% | 50 / 57 | 87.719% |
| 256 | 50% | 57 / 57 | 100.000% |
| 512 | 0% | 39 / 57 | 68.421% |
| 512 | 25% | 57 / 57 | 100.000% |
| 512 | 50% | 57 / 57 | 100.000% |

The selected 256-pixel candidate with 25% overlap contains:

```text
57 / 57 positive features with no context margin
57 / 57 positive features with a 160-metre context margin
50 / 57 positive features with a 320-metre context margin
```

## Geometry Evidence

Selected layout:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 25%
edge policy: SHIFT_TO_FIT
```

Measured geometry:

```text
tile count: 870
full tiles: 870
partial tiles: 0
coverage: 100.000%
uncovered source pixels: 0
padded output pixels: 0
repeated source observations: 25,640,304 pixels
total read expansion: 1.817x
```

Comparison with key alternatives:

| Tile | Stride | Overlap | Edge policy | Tiles | Coverage | Padding | Expansion |
|---:|---:|---:|---|---:|---:|---:|---:|
| 128 | 96 | 25% | SHIFT_TO_FIT | 3,420 | 100.000% | 0 | 1.786x |
| 256 | 256 | 0% | SHIFT_TO_FIT | 506 | 100.000% | 0 | 1.057x |
| 256 | 192 | 25% | SHIFT_TO_FIT | 870 | 100.000% | 0 | 1.817x |
| 256 | 128 | 50% | SHIFT_TO_FIT | 1,848 | 100.000% | 0 | 3.860x |
| 512 | 384 | 25% | SHIFT_TO_FIT | 210 | 100.000% | 0 | 1.755x |

## Label-Aware Evidence

Measured results for the selected layout:

```text
tile count: 870
supervised tiles: 50
positive tiles: 19
negative-only tiles: 31
all-ignore tiles: 820
positive tiles with at least 1% positive coverage: 11
positive tiles with at least 5% positive coverage: 2
positive-pixel coverage: 100.000000%
negative-pixel coverage: 100.000000%
positive observation multiplier: 1.479
padded ignore pixels: 0
```

Comparison with key alternatives:

| Tile | Overlap | Tiles | Supervised | Positive | Negative only | All ignore | Positive ≥1% | Positive ≥5% | Positive multiplier |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 25% | 3,420 | 103 | 30 | 73 | 3,317 | 27 | 16 | 1.717 |
| 256 | 0% | 506 | 27 | 12 | 15 | 479 | 9 | 1 | 1.000 |
| 256 | 25% | 870 | 50 | 19 | 31 | 820 | 11 | 2 | 1.479 |
| 256 | 50% | 1,848 | 107 | 40 | 67 | 1,741 | 31 | 7 | 4.000 |
| 512 | 25% | 210 | 25 | 8 | 17 | 185 | 5 | 0 | 1.405 |

Every evaluated candidate preserved all current positive and negative supervised pixels.

The primary differences were therefore:

- feature containment
- available context
- positive-label concentration
- tile population size
- observation duplication
- edge behavior
- computational expansion

## Edge-Policy Evidence

### DROP_PARTIAL

This policy left source pixels uncovered.

Depending on tile size, measured coverage ranged from:

```text
89.815% to 98.758%
```

Current supervision happened to remain covered, but unsupervised edge context was discarded.

### PAD_PARTIAL

This policy covered the full source grid but added artificial output pixels.

For the selected 256-pixel and 192-stride candidate:

```text
padded output pixels: 1,883,440
```

### SHIFT_TO_FIT

This policy produced:

```text
100% source coverage
0 padded output pixels
0 partial output tiles
```

Its cost is explicit repetition near raster boundaries.

This trade-off was selected for Loop 1.

## Selected Policy

The evidence supports:

```text
tile size: 256 × 256 pixels
stride: 192 × 192 pixels
overlap: 64 pixels
overlap percentage: 25%
edge policy: SHIFT_TO_FIT
```

This policy is implemented as:

```text
LOOP1_TILING_LAYOUT
```

## Reproduction Commands

```powershell
python scripts/check_real_tiling_layout_geometry.py
python scripts/check_real_tile_label_analysis.py
python scripts/check_real_positive_reference_scale.py
python scripts/check_real_positive_tile_containment.py
pytest tests/test_loop1_tiling_policy.py -q
pytest -q
git diff --check
```

## Automated Validation

At the time of evidence capture:

```text
52 focused tiling tests passed
375 total tests passed
git diff --check produced no errors
```

Real analysis results:

```text
candidate layout geometry: PASS
real label-aware tiling analysis: PASS
positive-reference scale analysis: PASS
actual positive-feature containment: PASS
```

## Scope Boundary

This evidence selects the deterministic candidate-window layout.

It does not:

- choose the final training samples
- materialize training image-label pairs
- balance positive and negative samples
- assign spatial splits
- create the final versioned dataset manifest

Those responsibilities remain in later phases.

## Evidence Result

```text
Code works: PASS
Tests pass: PASS
Real evidence exists: PASS
Decision is measurable: PASS
Selected policy is explicit: PASS
```

The Loop 1 tiling-policy decision is supported by real geometry, real labels, real positive-reference features, and reproducible automated analysis.