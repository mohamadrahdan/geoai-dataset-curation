# GeoAI Dataset Curation

A reproducible workflow for building, validating, versioning, and evaluating geospatial datasets for landslide segmentation using Sentinel-2 imagery and expert reference polygons.

## Project Status

The project is currently in **Loop 1**.

The repository foundation has been completed, and the project is moving toward the definition and validation of its first dataset contract.

No curated dataset or trained model has been released yet.

## Objective

This project implements the following iterative lifecycle:

```text
Reference Polygons
→ Curated Dataset
→ Baseline Model
→ Evaluation
→ Error Analysis
→ Expert Review
→ Improved Dataset
```

The purpose is not only to generate image and mask tiles.

The purpose is to create a traceable dataset-curation process in which source data, scientific decisions, dataset versions, model versions, evaluation results, and expert corrections remain connected.

## Loop 1 Scope

Loop 1 establishes the first small, real, and complete dataset-development cycle:

```text
Reference Polygons
→ padena_dataset_v1.0.0
→ padena_model_v1.0.0
→ evaluation_report_v1
→ error_analysis_v1
→ curation_report_v1
→ loop_2_backlog
```

The objective of Loop 1 is not to produce the best possible dataset or model.

Its objective is to establish a reproducible end-to-end process that can be tested, documented, evaluated, and improved in later loops.

## Study Area

The first dataset version focuses on the Padena region in Isfahan Province, Iran.

The available research inputs include:

- area-of-interest boundaries
- landslide polygons
- non-landslide polygons
- pseudo-landslide polygons

These source datasets are private and are not stored in this repository.

## Initial Machine-Learning Task

The initial task is binary semantic segmentation.

```text
0   = background / non-landslide
1   = landslide
255 = ignore / uncertain
```

Pseudo-landslide polygons are initially treated as hard-negative samples rather than as a separate output class.

This decision may be revised in later loops based on model errors and expert evaluation.

## Repository Responsibilities

This repository covers:

- research and dataset contracts
- source-data registration
- vector validation
- Sentinel-2 scene preparation
- image and label construction
- tiling and sampling
- image-mask pair generation
- quality control
- spatial dataset splitting
- dataset manifests and versioning
- training-package preparation
- baseline model training
- evaluation and error analysis
- curation reporting
- Loop 2 backlog preparation

## Repository Boundaries

This repository does not provide:

- production inference services
- frontend visualisation
- user-facing APIs
- private research-data distribution
- general GeoAI Platform backend functionality

The intended relationship between the main components is:

```text
Dataset Curation
→ Training & Evaluation
→ Approved Model
→ Production Inference
```

## Related Projects

### GeoAI Platform

The GeoAI Platform is responsible for production-oriented capabilities such as:

- model registration
- model-artifact management
- inference execution
- persistent run and result tracking
- APIs
- model integration
- result visualisation

This repository may later provide approved dataset versions, model artifacts, evaluation reports, and metadata to the platform.

### Legacy Prototype

The following repository is retained as a legacy prototype:

```text
gee-sentinel2-multiclass-dataset-generator
```

It demonstrated an earlier Google Earth Engine workflow for accessing Sentinel-2 imagery and generating tiles and masks.

Useful ideas may be reviewed and reimplemented, but this project does not depend on the legacy repository at runtime.

## Scientific Principles

The project follows these core principles:

- Reference polygons are treated as evidence rather than unquestionable ground truth.
- Model predictions do not automatically become new ground truth.
- Expert review is required before predictions enter a later dataset version.
- Training, validation, and test samples must be separated spatially.
- The frozen test set is used only at official evaluation gates.
- Tiling and sampling are treated as scientific design decisions.
- Dataset and model versions must remain traceable.
- Scientific decisions must be supported by measurable evidence.

## Dataset-Improvement Lifecycle

Later loops are expected to use the following feedback process:

```text
Model predictions
→ Candidate detections
→ Expert review
→ Confirmed / Corrected / Rejected / Uncertain
→ Improved dataset version
```

True positives, false positives, false negatives, and uncertain samples may all provide evidence for improving later dataset versions.

## Planned Loop 1 Outputs

The main planned artifacts are:

```text
padena_dataset_v1.0.0
padena_model_v1.0.0
evaluation_report_v1
error_analysis_v1
curation_report_v1
loop_2_backlog
```

These are planned artifact names and do not indicate that the artifacts have already been released.

## Project Structure

The repository currently contains the minimal foundation required for development:

```text
geoai-dataset-curation/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── decisions/
│       └── README.md
├── src/
│   └── geoai_dataset_curation/
│       └── __init__.py
├── tests/
│   └── test_package.py
├── .editorconfig
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

New directories and modules will be added only when required by an active development phase.

## Installation

Create and activate a Python virtual environment, then install the project in editable mode:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Tests

Run the automated tests with:

```powershell
pytest
```

The same installation and test process is executed through GitHub Actions.

## Data and Artifact Policy

Private data and large generated artifacts must not be committed to normal Git history.

Examples include:

- reference vectors
- Sentinel-2 raster products
- GeoTIFF files
- generated image and mask tiles
- NumPy arrays
- dataset releases
- model weights
- credentials
- temporary outputs

The repository may track lightweight reproducibility artifacts such as:

- source-data registries
- manifests
- checksums
- configuration files
- schemas
- quality-control summaries
- evaluation reports
- decision records
- small synthetic test fixtures

## Documentation

Important scientific and architectural decisions are stored in:

```text
docs/decisions/
```

Phase-level implementation evidence and closure notes may be stored in:

```text
docs/phases/
```

## License

Repository code and documentation are released under the MIT License unless stated otherwise.

This license does not automatically apply to:

- private reference polygons
- university-owned research data
- third-party datasets
- Sentinel-2 products
- generated dataset releases
- trained-model artifacts

Usage conditions for datasets and model artifacts will be documented separately when those artifacts are released.