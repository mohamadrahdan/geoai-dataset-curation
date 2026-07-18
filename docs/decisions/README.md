# Architecture and Research Decisions

This directory stores important scientific and architectural decisions for the GeoAI Dataset Curation project.

Decision records are created only when a choice has a meaningful effect on:

- scientific validity
- dataset semantics
- reproducibility
- spatial leakage
- model comparability
- artifact compatibility
- repository architecture
- future dataset loops

Routine implementation details do not require a separate decision record.

## Naming Convention

Decision files use the following format:

```text
DR-0001-short-decision-title.md
DR-0002-short-decision-title.md
```

Examples:

```text
DR-0001-use-binary-segmentation-label-contract.md
DR-0002-treat-pseudo-landslides-as-hard-negatives.md
DR-0003-use-spatially-separated-dataset-splits.md
```

## Decision Record Template

Each decision record should use the following structure:

```markdown
# DR-XXXX — Decision Title

## Status

Proposed | Accepted | Superseded | Rejected

## Context

What problem or risk required this decision?

## Decision

What was selected?

## Alternatives

What other options were considered?

## Consequences

What are the main benefits, limitations, or risks?

## Evidence

What test, metric, report, or observation supports the decision?

## Related Artifacts

Which files, datasets, reports, tests, or experiments are connected to it?
```

## Typical Decision Topics

Decision records may be created for topics such as:

- label semantics
- uncertain-area handling
- coordinate reference systems
- Sentinel-2 scene selection
- image construction
- label rasterization
- tiling
- sampling
- spatial splitting
- dataset versioning
- training configuration
- evaluation rules
- release gates

## Evidence

Important decisions should be supported by measurable evidence whenever possible.

Examples include:

- feature counts
- invalid-geometry counts
- class distributions
- spatial-overlap checks
- tile previews
- test results
- experiment results
- evaluation metrics
- error-analysis findings

## Scope

Decision records document important choices.

They do not replace:

- source-code documentation
- automated tests
- dataset manifests
- evaluation reports
- curation reports
- Git history