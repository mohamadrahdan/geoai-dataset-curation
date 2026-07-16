# GeoAI Dataset Curation

A reproducible dataset-curation workflow for building, validating, versioning, and evaluating geospatial datasets for landslide segmentation using Sentinel-2 imagery and expert reference polygons.

## Project status

The project is currently in:

```text
Loop 1
Phase L1-0 — Repository Foundation
```

No curated dataset or trained landslide model has been released yet.

## Project objective

The repository implements the following lifecycle:

```text
Reference Polygons
→ Curated Dataset
→ Baseline Model
→ Evaluation
→ Error Analysis
→ Expert Review
→ Improved Dataset
```

The goal is not only to generate image tiles.

The goal is to build a traceable curation system in which source data, scientific decisions, dataset versions, model versions, evaluation results, error samples, and expert corrections remain connected.

## Loop 1 scope

Loop 1 will produce the first complete dataset-curation and model-evaluation cycle:

```text
Reference Polygons
→ padena_dataset_v1.0.0
→ padena_model_v1.0.0
→ evaluation_report_v1
→ error_analysis_v1
→ curation_report_v1
→ loop_2_backlog
```

Loop 1 is intentionally designed as a small, real, and complete cycle.

Its purpose is not to create the best possible dataset or the most accurate possible model. Its purpose is to establish a reproducible end-to-end process that can be evaluated, documented, and improved in later loops.

## Initial study area

The first dataset version focuses on the Padena region in Isfahan Province, Iran.

The currently available source data includes:

- Padena area of interest
- landslide polygons
- non-landslide polygons
- pseudo-landslide polygons

These source datasets are private research inputs and are not stored in this repository.

## Initial machine-learning task

The initial task is:

```text
Binary semantic segmentation
```

The initial label contract is:

```text
0   = background / non-landslide
1   = landslide
255 = ignore / uncertain
```

Pseudo-landslide polygons are initially treated as a hard-negative source rather than as a separate model-output class.

This decision may be reviewed in later loops based on model errors, expert evaluation, and dataset evidence.

## Repository responsibilities

This repository owns the following responsibilities:

- research and dataset contracts
- source-data registration
- vector-data validation
- Sentinel-2 scene preparation
- image construction
- label rasterization
- tiling decisions
- sampling strategy
- image-mask pair generation
- quality-control checks
- spatial dataset splitting
- dataset manifests
- dataset versioning
- training-package preparation
- baseline model training
- model evaluation
- error analysis
- curation reporting
- Loop 2 backlog creation

## Repository boundaries

This repository does not own:

- the general GeoAI Platform backend
- production-facing inference services
- frontend visualisation
- user-facing APIs
- private research-data distribution
- the legacy Google Earth Engine prototype

Dataset curation, model training, and model evaluation remain separate from production inference.

The expected relationship between the main project components is:

```text
Dataset Curation
→ Training & Evaluation
→ Approved Model
→ Production Inference
```

## Related repositories

### GeoAI Platform

The GeoAI Platform is responsible for production-oriented capabilities such as:

- model registration
- model-artifact management
- inference execution
- persistent run and result tracking
- APIs
- plugin-based model integration
- future result visualisation

This repository produces versioned datasets, trained-model artifacts, evaluation reports, and metadata that may later be integrated into the platform.

### Legacy prototype

The following repository is retained as a legacy prototype:

```text
gee-sentinel2-multiclass-dataset-generator
```

The legacy repository demonstrated an early workflow for:

- reading geospatial class inputs
- accessing Sentinel-2 imagery
- creating image tiles
- creating masks
- exporting files through Google Earth Engine

Useful concepts may be reviewed and rewritten when needed.

However, this repository must not depend on the legacy project at runtime.

The new implementation must define its own contracts, tests, modules, decisions, and reproducibility rules.

## Scientific principles

The project follows these initial scientific principles:

- Reference polygons are evidence, not unquestionable ground truth.
- Model predictions do not directly become new ground truth.
- Expert review is required before predictions enter a later dataset version.
- Validation data supports repeated development decisions.
- The frozen test set is used only at official evaluation gates.
- Test-set results must not be used repeatedly to tune the model.
- Spatial leakage must be controlled explicitly.
- Training, validation, and test samples must be separated spatially.
- Tiling is treated as a scientific design decision rather than a simple image-cutting operation.
- True positives, false positives, and false negatives can all improve later dataset versions.
- Dataset versions and model versions must remain traceable.
- Scientific decisions must be documented together with measurable evidence.

## Tiling principles

Tiling decisions will be evaluated in a dedicated phase.

The following factors will be considered:

- tile size
- stride
- overlap
- edge policy
- spatial context
- class balance
- spatial leakage
- sampling strategy
- positive-pixel coverage
- negative-sample diversity
- hard-negative representation

No final tiling configuration has been selected at the current phase.

## Dataset-improvement lifecycle

Later loops are expected to use the following feedback process:

```text
model_v1 predictions
→ candidate detections
→ expert review
→ confirmed / corrected / rejected / uncertain
→ curated dataset_v2
```

Prediction categories may include:

```text
True Positive
False Positive
False Negative
Uncertain
```

Each category can provide evidence for improving future dataset versions.

## Loop 1 phases

Loop 1 is currently planned as:

```text
L1-0  Repository Foundation
L1-1  Research and Dataset Contract
L1-2  Source Data Registration
L1-3  Vector Validation
L1-4  Sentinel-2 Scene Preparation
L1-5  Image Construction
L1-6  Label Rasterization
L1-7  Tiling
L1-8  Sampling and Pair Generation
L1-9  Quality Control
L1-10 Spatial Split
L1-11 Manifest and Dataset Version
L1-12 Training Package
L1-13 Baseline Model Training
L1-14 Evaluation
L1-15 Error Analysis
L1-16 Release and Loop 2 Decision
```

A phase begins only after the previous phase has been completed and reviewed.

## Phase completion rule

A phase is complete only when:

```text
Code works
Tests pass
Artifact exists
Decision is documented
Evidence is measurable
```

Each phase must also include:

- a practical test
- an observable artifact
- documented scientific and architectural decisions
- measurable evidence
- a completion checklist
- LinkedIn-post potential assessment
- research-note potential assessment
- three-language interview preparation

The interview-preparation package will include:

```text
Phase-level explanation
Block-level interview Q&A
Follow-up question bank
Architecture storytelling
```

## Development workflow

The primary development environment includes:

- GitHub
- GitHub Desktop
- GitHub Web
- VS Code
- PowerShell
- Python
- GitHub Actions

Development follows a feature-branch workflow:

```text
main
→ feature branch
→ implementation
→ local test
→ commit
→ push
→ pull request
→ GitHub Actions
→ merge
→ remote branch deletion
→ local main synchronisation
→ local branch deletion
```

Significant project increments should use separate feature branches.

A phase may therefore contain more than one feature branch and more than one pull request.

## Continuous integration strategy

GitHub Actions will be introduced gradually.

The initial CI stages are expected to include:

```text
project installation
→ test execution
→ formatting checks
→ linting
→ type checking
→ coverage
→ geospatial and dataset-specific validation
```

Only the checks required by the current project maturity will be enabled.

More advanced checks will be added when the relevant code and data contracts exist.

## Repository growth policy

The repository structure grows incrementally.

Only directories required by the current phase or the next one or two immediate phases should be created.

Future folders must not be added only to make the repository appear complete.

This policy keeps responsibilities visible and prevents premature architecture.

## Current repository structure

At Phase L1-0, the repository contains only the initial foundation:

```text
geoai-dataset-curation/
├── docs/
│   └── decisions/
│       └── README.md
├── .editorconfig
├── .gitignore
├── LICENSE
└── README.md
```

Additional Python packages, tests, configuration files, workflows, and project directories will be added gradually during the remaining increments of Phase L1-0 and later phases.

## Data and artifact policy

Private research data and large generated artifacts must not be committed to normal Git history.

The repository excludes items such as:

- shapefiles
- GeoPackages
- GeoJSON research inputs
- GeoTIFF imagery
- Sentinel-2 raster products
- NumPy arrays
- model weights
- generated datasets
- credentials
- local environment files
- temporary outputs

The repository may later track lightweight and reproducible metadata such as:

- source-data registries
- manifests
- checksums
- configuration files
- schemas
- quality-control summaries
- evaluation reports
- decision records
- small synthetic test fixtures

## Planned Loop 1 outputs

The expected primary Loop 1 outputs are:

```text
padena_dataset_v1.0.0
padena_model_v1.0.0
evaluation_report_v1
error_analysis_v1
curation_report_v1
loop_2_backlog
```

These names describe planned artifacts.

They do not indicate that the artifacts already exist.

## Current limitations

At the current phase, the repository does not yet include:

- registered Padena source data
- validated vector layers
- Sentinel-2 scene definitions
- image composites
- rasterized labels
- image tiles
- mask tiles
- dataset splits
- dataset manifests
- training code
- a trained model
- evaluation metrics
- error samples
- a released dataset version

These capabilities will be introduced phase by phase.

## Documentation

Architecture and scientific decisions are stored in:

```text
docs/decisions/
```

Decision records will be created when a choice affects:

- scientific validity
- dataset semantics
- reproducibility
- spatial leakage
- artifact compatibility
- model comparability
- future loop design
- repository architecture

## License

Repository code and documentation are released under the MIT License unless stated otherwise.

This license does not automatically apply to:

- private reference polygons
- university-owned research data
- third-party datasets
- Sentinel-2 products
- generated dataset releases
- trained-model artifacts

Dataset and model usage conditions will be documented separately when those artifacts are released.