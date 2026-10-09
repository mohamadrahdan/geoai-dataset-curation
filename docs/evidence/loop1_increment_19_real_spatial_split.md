# Loop 1 Increment 19 — Real Spatial Split Evidence

## Status

Verified — 2026-10-09

## Objective

Generate and independently audit a deterministic, spatially separated train/validation/test assignment for the 50 quality-controlled Komeh image-mask pairs.

## Real Dataset

- Total verified pairs: 50
- Positive pairs: 19
- Negative-only pairs: 31
- Independent spatial groups: 3

## Spatial Group Composition

| Group | Total | Positive | Negative |
|---|---:|---:|---:|
| Large | 33 | 8 | 25 |
| Medium | 13 | 11 | 2 |
| Small | 4 | 0 | 4 |

## Approved Loop 1 Assignment

| Split | Total | Positive | Negative |
|---|---:|---:|---:|
| Train | 33 | 8 | 25 |
| Validation | 4 | 0 | 4 |
| Test | 13 | 11 | 2 |

The assignment preserves all three spatial groups without dividing a group across splits.

## Verification Evidence

- Assigned pairs: 50/50
- Independent spatial groups: 3
- Cross-split leakage violations: 0 under the selected zero-gap geometric criterion
- Automated tests: 630 passed
- Persisted catalog successfully written and verified

Catalog identity:

`sha256:b89670b7f0f19ffeca4ad4f9ff4be08b7ec9f55e1aba7b057e483f02b41bcf0f`

Local artifact:

`artifacts/live/loop1/komeh_spatial_split_v1.catalog.json`

## Reproduction

```powershell
python -B scripts/build_real_spatial_split.py
python -B scripts/check_real_spatial_split_options.py
python -m pytest -q
```

## Scientific Limitations

Only three spatially independent groups are available, and only two contain positive samples.

The validation split contains no positive samples and cannot support meaningful positive-class model selection.

The class distributions differ substantially between training and testing. Therefore, results must be interpreted as a limited spatial holdout experiment, not as evidence of general geographic transferability.

The independent audit establishes the absence of cross-split contact under the implemented geometric criterion, not complete statistical independence at all spatial scales.

## Loop 2 Direction

Increase the number and geographic diversity of verified reference samples, particularly spatially independent positive groups.

Retain a stable, independent evaluation reference when comparing model versions. Expanded training data must not contaminate the frozen test set.

## Conclusion

The spatial split is accepted for the limited Loop 1 baseline objective. The known dataset limitations are deliberately retained and documented rather than hidden or addressed through artificial balancing.