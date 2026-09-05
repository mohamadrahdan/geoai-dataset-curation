# Loop 1 Increment 12 — Image–Label Alignment Evidence

## Scope

This evidence record verifies direct spatial alignment between the physical Loop 1 Sentinel-2 image artifact and the physical label raster artifact.

The purpose is to prove that image pixels and label pixels share exactly the same spatial grid.

## Physical Artifacts

Image artifact:

```text
artifacts/live/loop1/komeh_sentinel2_2024_median.tif
```

Label artifact:

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

## Direct Alignment Verification

The two physical raster artifacts were inspected independently and compared directly.

Observed results:

```text
CRS matches: True
Width matches: True
Height matches: True
Transform matches: True
```

Both rasters have:

```text
width: 5712
height: 5493
CRS: EPSG:32639
```

Their affine transforms are identical:

```text
(10.0, 0.0, 533040.0,
 0.0, -10.0, 3451350.0)
```

## Verification Result

```text
PASS: Physical image and label rasters are exactly pixel-aligned.
```

## Architectural Meaning

The verification proves the physical relationship:

```text
image pixel (row, col)
        ↕
label pixel (row, col)
```

Both pixels refer to the same spatial footprint.

This is stronger than validating each artifact independently against the approved grid because the final physical image and label files are compared directly.

## Scope Boundary

This increment verifies spatial alignment only.

It intentionally does not require the image and label artifacts to have the same:

```text
band count
dtype
semantic values
```

Those properties belong to their separate artifact contracts.

Label-distribution analysis and spatial supervision quality control belong to:

```text
L1-6B.4 — Label Statistics & Spatial QC
```