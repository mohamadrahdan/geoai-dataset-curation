# Loop 1 Increment 20 — Dataset Release Evidence

## Status

Completed — 2026-10-10

## Objective

Package the verified Komeh image-mask pairs into a versioned, portable dataset release that can be consumed by the baseline model training pipeline.

## Dataset Release

- Dataset version: `padena_dataset_v1.0.0`
- Study area: Komeh, Padena, Isfahan
- Total verified image-mask pairs: 50
- Positive pairs: 19
- Verified-negative-only pairs: 31
- Spatial leakage groups: 3

## Approved Spatial Split

| Split | Total | Positive | Negative-only |
|---|---:|---:|---:|
| Train | 33 | 8 | 25 |
| Validation | 4 | 0 | 4 |
| Test | 13 | 11 | 2 |
| Total | 50 | 19 | 31 |

The split preserves complete spatial groups. No group is divided between training, validation, and test.

## Release Contents

The release contains:

- `manifest.json`
- Three split files: `train.json`, `validation.json`, and `test.json`
- 50 image tiles
- 50 corresponding mask tiles
- Automated pair-quality-control evidence
- Human visual-review evidence
- Spatial split evidence

The manifest tracks 106 files using SHA-256 checksums. The manifest itself is not included in its own checksum inventory.

## Provenance

Source pair catalog ID:

`sha256:7a1a0996917a58ec071dde6fc5982c89dd605f5996b02749b8af39d676724b4b`

The release preserves references to the source pair catalog and spatial split evidence.

## Validation Results

The following checks completed successfully:

- Release input readiness
- Physical image and mask presence
- Pair and tile identity consistency
- Split membership and class distribution
- Spatial group integrity
- File inventory and SHA-256 checksums
- Relative file paths
- Portable release validation after relocation

The completed release validation reported:

- 50 assigned pairs
- 3 spatial groups
- 106 verified files
- Successful validation after copying the release to another directory

The previously executed full project suite reported 630 passing tests.

## Reproduction Commands

```powershell
python -B scripts/check_dataset_release_inputs.py
python -B scripts/build_dataset_release.py
python -B scripts/validate_dataset_release.py --check-relocation
python -m pytest -q
```

The build command creates a new release and intentionally refuses to overwrite an existing release directory. It must not be rerun against the already-created version without using a separate, controlled output location.

## Scientific and Technical Limitations

1. Only three spatial groups are available.
2. The validation split contains no positive samples.
3. The test split must remain excluded from training and model selection.
4. Geometric separation under the selected criterion does not prove complete statistical independence.
5. Package integrity and relocation have been verified, but independent reconstruction of an identical release from the original inputs has not yet been demonstrated.
6. Actual model training from the packaged release remains to be verified in the baseline modeling phase.

## Outcome

`padena_dataset_v1.0.0` has been built and validated as a portable, versioned dataset package.

The release is ready to be used as the input for baseline model development, subject to the documented scientific limitations.