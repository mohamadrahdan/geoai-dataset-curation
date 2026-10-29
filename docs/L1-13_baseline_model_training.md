# L1-13 — Baseline Model Training

## Objective

Establish a reproducible, framework-specific training baseline using the immutable `padena_dataset_v1.0.0` release, without accessing the frozen test split.

## Implementation

- Architecture: Small U-Net
- Input: Four Sentinel-2 bands (`B2`, `B3`, `B4`, `B8`)
- Output: One binary segmentation logit per pixel
- Activation: LeakyReLU, negative slope 0.1
- Loss: Ignore-aware binary cross-entropy
- Label contract: 0 = verified negative, 1 = landslide, 255 = ignore
- Optimizer: Adam
- Learning rate: 0.001
- Batch size: 2
- Training epochs: 10
- Random seed: 42
- Checkpoint policy: Final epoch only

## Training Data

The training split contains 33 image-mask pairs:

- Positive-labeled pixels: 11,588
- Verified negative pixels: 100,305
- Ignored pixels: 2,050,795

No validation or test samples were used for training or checkpoint selection.

## Diagnostic Findings

The initial ReLU model produced nearly constant predictions and exhibited zero gradient in its first convolutional layer.

Changing the activation to LeakyReLU restored early-layer gradient flow.

A controlled single-tile overfitting experiment reached a supervised-pixel IoU of 1.0 after 300 optimization steps. This demonstrated that the network could learn the labeled spatial pattern of one training tile, but did not establish generalization.

Additional full-training experiments were conducted with 30 epochs and class-weighted BCE. Neither demonstrated reliable class separation across the complete training split.

## Selected Engineering Baseline

The 10-epoch LeakyReLU model trained with unweighted masked BCE was retained as the simplest functional engineering baseline.

Train-only diagnostics:

- Final checkpoint BCE: 0.339382
- Constant-probability BCE reference: 0.332842
- Train ROC-AUC: 0.408025

These results indicate weak class discrimination on the training data. They must not be presented as validated segmentation performance.

## Model Artifact

Local artifact directory:

`artifacts/models/padena_model_v1.0.0/`

Files:

- `model.pt`: Model state dictionary
- `model.json`: Model configuration, source dataset metadata, training settings, and weights checksum

Artifacts are excluded from Git and require separate preservation.

## Reproduction

Run training against the same immutable dataset release:

```powershell
python -B scripts/train_baseline.py `
  --activation leaky_relu `
  --epochs 10 `
  --output artifacts/models/padena_model_rebuild
```

The selected output directory must not already exist.

## Verification

- Baseline model tests: 10 passed
- Complete repository test suite: 647 passed
- Saved weights checksum: Verified
- Saved model reload: Successful

## Limitations

- Training data is small and highly imbalanced.
- Most raster pixels are ignored during supervised training.
- The selected baseline has not demonstrated reliable class discrimination.
- The validation split contains no positive-labeled samples.
- No independent test-set evaluation has been conducted.

## Handoff to L1-14

The model is ready for independent evaluation as an engineering baseline, not as a validated landslide detection model.

L1-14 must report performance limitations transparently, preserve the frozen test protocol, and avoid making post-test model or threshold adjustments based on test results.
