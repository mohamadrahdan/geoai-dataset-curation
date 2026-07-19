# DR-0001 — Use a Binary Segmentation Label Contract

## Status

Accepted

## Context

Loop 1 requires a clear and stable label definition before source validation, rasterization, tiling, training, and evaluation can begin.

The available reference data includes landslide, non-landslide, pseudo-landslide, and uncertain areas.

A multi-class formulation would add complexity before sufficient evidence exists to justify separate output classes.

## Decision

Loop 1 uses binary semantic segmentation with the following label values:

```text
0   = background / non-landslide
1   = landslide
255 = ignore / uncertain
```

Pseudo-landslide areas are treated as hard-negative evidence and receive label value `0`.

Uncertain or unresolved areas receive label value `255` and are excluded from training loss and official metric calculations.

## Alternatives

The following alternatives were considered:

- multi-class segmentation with a separate pseudo-landslide class
- excluding pseudo-landslide areas completely
- forcing uncertain areas into positive or negative labels

These alternatives were not selected for Loop 1 because they would either increase complexity or introduce weak labels.

## Consequences

This decision provides a simple and testable model-output contract.

It also allows difficult negative examples to remain in the dataset without introducing an additional output class.

The main limitation is that pseudo-landslide behavior cannot be evaluated as a separate prediction category.

## Evidence

The decision is based on the current source-data categories, the small scope of Loop 1, and the need for a reproducible baseline.

It will be reviewed after validation results and model-error analysis become available.

## Related Artifacts

- `docs/contracts/dataset-contract.md`
- future label-rasterization configuration
- future dataset manifest
- future evaluation report