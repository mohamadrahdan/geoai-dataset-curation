# DR-0006: Introduce an Earth Engine Provider Boundary

## Status

Accepted

## Context

The image-construction workflow will eventually use Google Earth Engine to search for Sentinel-2 scenes, build composites, start exports, and check task status.

Using the Earth Engine SDK directly throughout the Dataset Curation code would make the core workflow dependent on `ee` objects, authentication, network access, and provider-specific exceptions. It would also make ordinary tests slower and harder to control.

## Decision

We introduced an `EarthEngineProvider` protocol between the Dataset Curation workflow and Earth Engine.

The project now works with its own small contracts for scene queries, scene references, composites, image references, exports, and task statuses. Earth Engine objects remain inside the future real provider implementation.

An `EarthEngineService` validates requests before passing them to the provider. A configurable `FakeEarthEngineProvider` supports deterministic tests without credentials or internet access.

Provider-specific failures will be translated into a small set of internal Earth Engine errors.

## Why this works for us

This keeps the main workflow independent of the Earth Engine SDK and gives us one stable place for validation and error handling.

It also means we can develop and test the orchestration now, then add authentication and the real provider adapter later without redesigning the domain contracts.

The trade-off is a little more adapter code, but the separation is valuable because Earth Engine is an external service with its own objects, failures, quotas, and task lifecycle.

## Scope

This decision defines the provider boundary only.

Real authentication, Earth Engine initialization, Sentinel-2 queries, composite construction, and export execution will be added in later increments.

## Evidence

The provider contracts, fake provider, validation service, and normalized errors are covered by the automated test suite.

At the time of this decision, all 124 tests pass.