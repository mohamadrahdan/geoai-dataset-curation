# Dataset Contract

## Purpose

This contract defines(definiert) the initial scientific and technical rules for the first curated landslide-segmentation dataset.

It provides(stellt bereit) a shared reference for later phases such as source-data registration, validation, rasterization, tiling, sampling, training, and evaluation.

## Study Area

The initial dataset focuses(konzentriert sich) on the Padena region in Isfahan Province, Iran.

## Task Definition

The initial machine-learning task is(ist):

```text
Binary semantic segmentation
```

The model must predict(vorhersagen) whether each valid pixel belongs to a landslide or to the background.

## Label Contract

The initial label values are(sind):

```text
0   = explicit negative training target
1   = positive landslide target
255 = ignore
```

Unannotated pixels are not automatically treated as negative evidence.

The supervision source remains distinct from the numeric training target:

```text
positive reference      -> 1
reviewed negative       -> 0
hard negative           -> 0
unlabeled               -> 255
nodata                  -> 255
```

Label value `255` is excluded(wird ausgeschlossen) from loss calculation and official metric calculation.

## Source Polygon Roles

### Landslide Polygons

Landslide polygons represent(repräsentieren) positive reference areas.

They are treated(werden behandelt) as evidence for label value `1`.

### Non-Landslide Polygons

Non-landslide polygons represent(repräsentieren) reviewed negative reference areas.

They are treated(werden behandelt) as evidence for label value `0`.

### Pseudo-Landslide Polygons

Pseudo-landslide polygons represent(repräsentieren) visually or geomorphologically similar areas that are not accepted as landslides.

In Loop 1, they are treated(werden behandelt) as hard-negative evidence and receive label value `0`.

They are not used(werden nicht verwendet) as a separate model-output class.

## Uncertain Areas

Areas with unclear, conflicting, incomplete, or unreliable interpretation are assigned(erhalten) label value `255`.

Uncertain areas are not converted(werden nicht umgewandelt) automatically into positive or negative training labels.

## Inclusion Rules

A source feature may enter(kann aufgenommen werden) the curated workflow only when:

- its geometry is readable
- its geometry type is supported
- its spatial reference is known
- its source category is known
- its role in the label contract is explicit
- it passes the required validation checks

## Exclusion Rules

A source feature must be excluded(muss ausgeschlossen werden) or marked as uncertain when:

- the geometry is invalid and cannot be repaired reliably
- the class meaning is unknown
- the spatial reference is missing or ambiguous
- the feature lies outside the accepted study area
- the feature conflicts with another label source and the conflict cannot be resolved
- the evidence is too weak for a positive or negative label


## Pair Quality-Control Policy

Every materialized image-mask pair must pass automated quality control and complete human visual review before spatial split assignment.

Automated quality control must verify:

- raster existence and readability
- image and mask dimensions
- CRS and affine-transform agreement
- expected image band count and dtype
- finite and non-empty image content
- allowed mask values and expected label semantics
- pair identity and cross-artifact traceability
- complete coverage of expected image and mask files

The automated results must be persisted as a structured report linked to the exact image-mask pair catalog.

Human visual review must include every pair and must inspect the image, colorized mask, and image-mask overlay.

Every human decision must be persisted and linked to the exact pair identity.

A pair population may proceed to spatial splitting only when:

- the automated report status is `pass`
- traceability status is `pass`
- every expected pair is verified
- no human review remains `pending`
- no human decision is `review` or `fail`
- every expected pair has a human `pass` decision

Quality control must be completed before split membership is assigned.


## Spatial Split Policy

Training, validation, and test samples must be separated(müssen getrennt werden) spatially.

Random tile-level splitting is not sufficient(ist nicht ausreichend) when neighboring tiles may share the same landscape context.

The exact split method will be defined(wird definiert) in the dedicated spatial-split phase.

## Frozen Test Set Policy

The official test set will be frozen(wird eingefroren) before final model evaluation.

It must not be used(darf nicht verwendet werden) repeatedly for model tuning, threshold selection, or routine development decisions.

## Traceability

Each dataset release must remain(muss bleiben) traceable to:

- source-data records
- validation results
- processing configuration
- label rules
- spatial split definition
- dataset manifest
- dataset version
- related model version
- evaluation report

## Initial Dataset Version

The first planned dataset release is(ist):

```text
padena_dataset_v1.0.0
```

This file defines(definiert) the initial contract only.

It does not indicate(bedeutet nicht), that the dataset has already been generated or released.

## Review Policy

This contract may be revised(kann überarbeitet werden) only when new evidence, validation results, expert review, or model-error analysis justifies a change.

Any important change must be documented(muss dokumentiert werden) as a new decision record or a versioned contract update.