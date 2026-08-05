# DR-0007: Keep Earth Engine authentication behind a runtime boundary

## Decision

Earth Engine configuration, credential selection, initialization, and SDK access are kept behind explicit internal contracts.

Only `EarthEngineSdkRuntime` imports and calls the real Earth Engine Python SDK. The rest of the image-construction workflow depends on the SDK-neutral `EarthEngineRuntime` protocol.

Interactive authentication is not triggered automatically during application startup. Local authentication remains an explicit user action, while initialization consumes credentials that are already available.

## Why

This keeps unit tests deterministic and independent of internet access, Google accounts, regional access conditions, and live Earth Engine availability.

It also prevents SDK-specific behavior and exceptions from spreading through the dataset-curation workflow.

## Operational note

Local Google authorization was completed successfully during development. Live initialization could not yet complete because no registered Earth Engine Cloud Project was available.

This is treated as an external runtime prerequisite rather than a failure of the internal implementation.

## Consequences

- Unit tests use injected fake SDK implementations.
- SDK exceptions are translated into project-level errors.
- A valid registered Cloud Project must be supplied for live execution.
- Credentials, tokens, and service-account key files must remain outside the repository.