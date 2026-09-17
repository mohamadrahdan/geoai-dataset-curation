# Phase Documentation

This directory stores short phase-level records for the GeoAI Dataset Curation project.

Each file documents what was actually completed in one project phase.

Phase documents are intended to provide a concise record of:

- the phase objective
- implemented work
- practical verification
- produced artifacts
- important decisions
- measurable evidence
- remaining limitations
- readiness for the next phase

They should not repeat the full project description, development workflow, or complete Loop 1 plan from the main `README.md`.

## Tracked Phase Records

- [L1-5B â€” Real Image Construction](L1-5B-real-image-construction.md)
- [L1-6A â€” Label Rasterization Contracts](L1-6A-label-rasterization-contracts.md)
- [L1-6B â€” Real Label Rasterization and Alignment](L1-6B-real-label-rasterization-and-alignment.md)
- [L1-7A â€” Tiling Contracts](L1-7A-tiling-contracts.md)
- [L1-7B â€” Tiling Policy Selection](L1-7B-tiling-policy-selection.md)
- [L1-7C â€” Candidate Tile Catalog](L1-7C-candidate-tile-catalog.md)
- [L1-8 â€” Sampling and Image-Mask Pair Generation](L1-8-sampling-and-image-mask-pair-generation.md)

## Naming Convention

Phase files use the following format:

```text
L1-0-repository-foundation.md
L1-1-research-and-dataset-contract.md
L1-2-source-data-registration.md
```

## Phase Record Template

Each phase file should use the following structure:

```markdown
# Phase L1-X â€” Phase Title

## Status

Completed | In Progress | Blocked

## Objective

What was this phase intended to establish or produce?

## Implemented Work

What was actually created, changed, or validated?

## Practical Verification

Which commands, tests, inspections, or experiments were performed?

## Artifacts

Which files, reports, datasets, configurations, or other outputs were produced?

## Decisions

Which important scientific or architectural decisions were made?

## Measurable Evidence

What concrete results demonstrate completion?

## Limitations

What is intentionally not included or still unresolved?

## Completion Checklist

- [ ] Code or workflow works
- [ ] Tests or practical checks pass
- [ ] Required artifact exists
- [ ] Important decisions are documented
- [ ] Evidence is measurable

## Next Phase

What is the next immediate phase?
```

## Scope

Phase records should remain concise and focused on completed work.

They do not replace:

- the main project `README.md`
- architecture and research decision records
- source-code documentation
- automated tests
- dataset manifests
- evaluation reports
- curation reports
- Git and Pull Request history

## Documentation Principle

A phase document should describe the final verified state of the phase.

It should not become a detailed daily log of every command, correction, or intermediate attempt.