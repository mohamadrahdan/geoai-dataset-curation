# Loop 1 Increment 11 — Real Label Rasterization Evidence

## Scope

This evidence record documents the first real rasterization of the Loop 1 reference labels.

The increment converts validated real reference polygons into a physical GeoTIFF label raster using the approved Loop 1 rasterization contract.

## Real Inputs

The rasterization uses the three real reference groups prepared in L1-6B.1:

```text
57 positive-reference features
54 negative-reference features
49 hard-negative-reference features
160 total features
```

The sources are validated, repaired where necessary, and reprojected to:

```text
EPSG:32639
```

before rasterization.

## Approved Raster Grid

The label raster uses the same approved exact grid established for the real Sentinel-2 image:

```text
CRS: EPSG:32639
width: 5712
height: 5493
pixel size: 10 m
```

Affine transform:

```text
(10.0, 0.0, 533040.0,
 0.0, -10.0, 3451350.0)
```

## Rasterization Semantics

The Loop 1 training-target mapping is:

```text
POSITIVE_REFERENCE      -> 1
NEGATIVE_REFERENCE      -> 0
HARD_NEGATIVE_REFERENCE -> 0
UNLABELED                -> 255
```

The raster is initialized with:

```text
IGNORE = 255
```

Only explicit supervision overwrites the initial ignore value.

This preserves the rule:

```text
UNLABELED != NEGATIVE
```

## Rasterization Policy

The real execution follows the approved Loop 1 policy:

```text
pixel inclusion     -> pixel center
initial fill        -> IGNORE = 255
conflicting overlap -> error
partial outside     -> clip to grid
fully outside       -> reject
```

No conflicting positive-versus-negative overlap caused the real execution to fail.

## Physical Artifact

The generated real label artifact is:

```text
artifacts/live/loop1/komeh_labels_v1.tif
```

The rasterization execution reported:

```text
Shape: (5493, 5712)
Dtype: uint8
Burned feature count: 160
```

## Observed Pixel Values

The real raster contains:

```text
value 0   -> 64,388 pixels
value 1   -> 17,933 pixels
value 255 -> 31,293,695 pixels
```

The complete raster therefore contains:

```text
31,376,016 pixels
```

Only the approved values are present:

```text
{0, 1, 255}
```

## Artifact Verification

The physical GeoTIFF was independently inspected and verified against the L1-6A artifact contract.

Verification results:

```text
CRS matches: True
Width matches: True
Height matches: True
Transform matches: True
Band count matches: True
Dtype matches: True
Values valid: True
Observed values: (0, 1, 255)
```

Final verification result:

```text
PASS
```

The physical artifact therefore satisfies the approved label-raster contract.

## Architectural Result

The real execution now proves this path:

```text
real private reference vectors
↓
controlled validation and repair
↓
reprojection to approved CRS
↓
LabelVectorSource
↓
LabelRasterizationRequest
↓
Loop 1 rasterization policy
↓
uint8 label array
↓
physical GeoTIFF
↓
artifact contract verification
```

## Measurable Evidence

The increment proves that:

```text
160 real reference features were processed
the label raster has exactly 31,376,016 pixels
the raster uses the approved exact grid
the raster is single-band uint8
only values 0, 1, and 255 are present
unlabeled pixels remain IGNORE
the physical GeoTIFF passes the artifact contract
```

## Scope Boundary

This increment proves that the real label artifact is valid against its own approved grid contract.

It does not yet independently compare the physical label GeoTIFF with the physical Sentinel-2 GeoTIFF.

That direct image-label artifact comparison belongs to:

```text
L1-6B.3 — Image–Label Alignment Verification
```

Class-distribution analysis and spatial quality control belong to:

```text
L1-6B.4 — Label Statistics & Spatial QC
```