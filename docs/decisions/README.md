# Architecture and Research Decisions

This directory stores short, version-controlled decision records for the
GeoAI Dataset Curation project.

A decision record is required when a choice affects one or more of the
following:

- scientific validity
- dataset semantics
- reproducibility
- spatial leakage
- artifact compatibility
- model comparability
- future loop design
- repository architecture

## Why Decision Records Exist

Dataset-curation projects contain many choices that may look technical but
directly influence scientific validity.

Examples include:

- how uncertain polygons are handled
- which coordinate reference system is used
- how Sentinel-2 scenes are selected
- how masks are rasterized
- how tiles overlap
- how negative samples are selected
- how spatial leakage is prevented
- when the frozen test set is used

These decisions must remain visible, reviewable, and connected to measurable
evidence.

## Decision Record Naming

Decision files use the following format:

```text
DR-0001-short-decision-title.md
DR-0002-short-decision-title.md
DR-0003-short-decision-title.md
```

Examples:

```text
DR-0001-use-binary-segmentation-label-contract.md
DR-0002-treat-pseudo-landslides-as-hard-negatives.md
DR-0003-use-spatially-separated-dataset-splits.md
```

## Minimum Decision Record Structure

Each decision record should use the following structure:

```markdown
# DR-XXXX — Decision Title

## Status

Proposed | Accepted | Superseded | Rejected

## Context

What problem, risk, or uncertainty required a decision?

## Decision

What option was selected?

## Alternatives Considered

What other options were considered?

## Consequences

What does this decision make easier, harder, safer, or more limited?

## Evidence

What measurable evidence supports or evaluates the decision?

## Related Artifacts

Which reports, manifests, datasets, tests, or source files are connected to
this decision?
```

## Decision Categories

Decision records may cover:

- repository architecture
- research contracts
- source-data handling
- coordinate reference systems
- spatial resolution
- Sentinel-2 scene selection
- image construction
- label semantics
- rasterization
- tiling
- sampling
- quality control
- spatial splitting
- dataset versioning
- training configuration
- model evaluation
- error analysis
- release gates

## Status Meanings

### Proposed

The decision is being discussed or tested but is not yet final.

### Accepted

The decision is currently active and should be followed by the project.

### Superseded

A newer decision record has replaced this decision.

### Rejected

The option was evaluated but was not selected.

## Evidence Principle

A decision should not be accepted only because it sounds reasonable.

Whenever possible, it should be supported by evidence such as:

- validation statistics
- geometry counts
- invalid-feature counts
- class distributions
- spatial-overlap checks
- tile previews
- experiment results
- evaluation metrics
- error-analysis findings
- reproducible test outputs

## Scope

Decision records document important choices.

They do not replace:

- source-code documentation
- test cases
- dataset manifests
- evaluation reports
- curation reports
- Git commit history