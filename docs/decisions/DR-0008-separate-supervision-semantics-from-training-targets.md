# DR-0008: Separate Supervision Semantics from Training Targets

## Status

Accepted

Supersedes the background interpretation in DR-0001 while preserving the binary segmentation objective.

## Context

Loop 1 uses binary semantic segmentation for landslide detection.

The earlier label contract defined:

```text
0   = background / non-landslide
1   = landslide
255 = ignore / uncertain
```

That contract was sufficient as an initial baseline, but later review of the available reference data identified an important limitation.

The current reference inventory is spatially incomplete. The absence of a reference polygon does not prove that a pixel is a reviewed non-landslide location.

Treating every unannotated pixel as background would therefore introduce false-negative supervision and could also increase the dominance of negative pixels during training.

The available supervision sources have different meanings:

- landslide polygons are positive reference evidence
- non-landslide polygons are explicitly reviewed negative evidence
- pseudo-landslide polygons are hard-negative evidence
- unannotated areas have unknown supervision
- nodata areas do not contain valid training observations

These meanings must remain distinguishable even when multiple supervision types map to the same binary training target.

## Decision

Loop 1 separates supervision semantics from training-target values.

The training-target contract remains binary:

```text
NEGATIVE = 0
POSITIVE = 1
IGNORE   = 255
```

The supervision contract is:

```text
POSITIVE_REFERENCE
NEGATIVE_REFERENCE
HARD_NEGATIVE_REFERENCE
UNLABELED
NODATA
```

The mapping is:

| Supervision kind | Training target | Contributes to loss |
| --- | ---: | --- |
| `POSITIVE_REFERENCE` | `POSITIVE` | yes |
| `NEGATIVE_REFERENCE` | `NEGATIVE` | yes |
| `HARD_NEGATIVE_REFERENCE` | `NEGATIVE` | yes |
| `UNLABELED` | `IGNORE` | no |
| `NODATA` | `IGNORE` | no |

The key semantic rule is:

```text
UNLABELED != NEGATIVE
```

The absence of an annotation must not automatically be interpreted as negative evidence.

Hard-negative areas remain binary negative targets but retain a distinct supervision identity so that later sampling and quality-control stages can treat them differently from ordinary reviewed negatives.

Unlabeled and nodata pixels both map to `IGNORE` for training, but their semantic reasons remain distinct.

## Consequences

### Positive consequences

- incomplete reference coverage does not automatically create false-negative labels
- hard negatives remain available for later sampling strategies
- binary model output remains simple
- supervision provenance is preserved
- later tiling and sampling can distinguish ordinary negatives from hard negatives
- ignored pixels can be excluded from loss and official metrics
- nodata and unknown supervision remain distinguishable for quality control

### Trade-offs

- the label contract becomes richer than a simple three-value enum
- later rasterization must preserve supervision semantics before collapsing them into training targets
- dataset statistics must distinguish ignored pixels from valid negatives
- training code must respect the ignore value consistently
- later manifests may need to persist both target values and supervision provenance

## Alternatives Considered

### Treat all unannotated pixels as background

Rejected because the reference inventory is incomplete and absence of annotation is not reliable negative evidence.

### Use pseudo-landslides as a separate model-output class

Rejected for Loop 1 because the primary task remains binary landslide segmentation.

Pseudo-landslides are more useful as hard-negative supervision than as a separate prediction class at this stage.

### Collapse unlabeled and nodata into one semantic category

Rejected because both are ignored during training for different reasons.

Unlabeled pixels lack supervision, while nodata pixels lack valid source data.

## Relationship to DR-0001

DR-0001 established the initial binary segmentation objective and remains valid in that respect.

This decision refines its interpretation of the negative/background class.

The updated rule is:

```text
0 = explicit negative training target
1 = positive landslide target
255 = ignored training target
```

Value `0` must no longer be interpreted as every pixel that is not inside a landslide polygon.

## Evidence

The implementation now includes:

- `LabelValue`
- `SupervisionKind`
- `LabelSchemaEntry`
- `LOOP1_LABEL_SCHEMA`
- explicit supervision-to-target mapping
- tests confirming that unlabeled pixels do not become negative targets
- tests preserving hard-negative identity
- tests distinguishing unlabeled and nodata semantics

At the time of this decision:

```text
10 focused label-schema tests pass
265 total tests pass
```

## Future Use

This contract will be consumed by later stages including:

```text
vector-to-raster conversion
rasterization policy
label artifact generation
image-label alignment
tiling
sampling
training
evaluation
```

Later loops may revise the schema if model-error analysis or new reference data justifies a different supervision strategy.