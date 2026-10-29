"""Tests for the baseline model and ignored-label loss."""

import pytest

torch = pytest.importorskip("torch")

from geoai_dataset_curation.baseline_model import (
    SmallUNet,
    masked_bce_loss,
)


def test_forward_shape():
    model = SmallUNet()

    with torch.no_grad():
        prediction = model(
            torch.randn(2, 4, 32, 32)
        )

    assert prediction.shape == (2, 1, 32, 32)
    assert torch.isfinite(prediction).all()


def test_masked_loss_ignores_unlabeled_values():
    logits = torch.tensor(
        [[[[0.0, -7.0], [1.0, 12.0]]]],
        requires_grad=True,
    )

    masks = torch.tensor(
        [[[1, 255], [0, 255]]]
    )

    loss = masked_bce_loss(logits, masks)

    expected = (
        torch.nn.functional.binary_cross_entropy_with_logits(
            torch.tensor([0.0, 1.0]),
            torch.tensor([1.0, 0.0]),
        )
    )

    assert torch.allclose(loss, expected)

    loss.backward()

    assert logits.grad[0, 0, 0, 1].item() == 0
    assert logits.grad[0, 0, 1, 1].item() == 0
    assert logits.grad[0, 0, 0, 0].item() != 0


def test_unlabeled_only_batch_is_rejected():
    with pytest.raises(
        ValueError,
        match="no supervised",
    ):
        masked_bce_loss(
            torch.zeros(1, 1, 4, 4),
            torch.full((1, 4, 4), 255),
        )


def test_bad_label_is_rejected():
    with pytest.raises(
        ValueError,
        match="0, 1, or 255",
    ):
        masked_bce_loss(
            torch.zeros(1, 1, 2, 2),
            torch.tensor(
                [[[1, 0], [2, 255]]]
            ),
        )


def test_shape_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match="dimensions",
    ):
        masked_bce_loss(
            torch.zeros(1, 1, 4, 4),
            torch.zeros(1, 5, 5),
        )


def test_model_weights_round_trip(tmp_path):
    torch.manual_seed(5)
    model = SmallUNet()
    model.eval()
    example = torch.randn(1, 4, 16, 16)

    with torch.inference_mode():
        output = model(example)

    path = tmp_path / "model.pt"
    torch.save(model.state_dict(), path)
    copy = SmallUNet()
    copy.load_state_dict(
        torch.load(
            path,
            weights_only=True,
            map_location="cpu",
        )
    )

    copy.eval()

    with torch.inference_mode():
        assert torch.allclose(
            copy(example),
            output,
        )

def test_leaky_relu_propagates_early_gradients():
    "Verify gradient flow to the first convolutional layer."
    torch.manual_seed(42)
    model = SmallUNet(
        in_channels=4,
        base_channels=8,
        activation="leaky_relu",
    )
    assert isinstance(
        model.enc1[1],
        torch.nn.LeakyReLU,
    )
    assert model.enc1[1].negative_slope == 0.1

    # Synthetic four-band image
    images = torch.rand(1, 4, 32, 32) * 0.5 + 0.05

    # Synthetic mask
    masks = torch.zeros(
        (1, 32, 32),
        dtype=torch.long,
    )
    masks[:, 8:16, 8:16] = 1
    masks[:, 20:, 20:] = 255
    model.train()
    model.zero_grad(set_to_none=True)
    logits = model(images)
    assert logits.shape == (1, 1, 32, 32)
    loss = masked_bce_loss(logits, masks)
    assert torch.isfinite(loss).item()
    loss.backward()

    # Explicitly verify the first layer type
    first_conv = model.enc1[0]

    assert isinstance(
        first_conv,
        torch.nn.Conv2d,
    )

    # Extract gradients
    first_grad = first_conv.weight.grad
    output_grad = model.out.weight.grad

    # Explicit type narrowing for Pylance
    assert isinstance(first_grad, torch.Tensor)
    assert isinstance(output_grad, torch.Tensor)

    # Check gradient validity
    assert torch.isfinite(first_grad).all().item()
    assert torch.isfinite(output_grad).all().item()

    # Check non-zero gradient flow
    first_norm = torch.linalg.vector_norm(first_grad).item()
    output_norm = torch.linalg.vector_norm(output_grad).item()

    assert first_norm > 0.0
    assert output_norm > 0.0

def test_original_relu_remains_default():
    "Verify backward compatibility with the original ReLU model."
    original = SmallUNet()
    modified = SmallUNet(activation="leaky_relu")
    assert isinstance(original.enc1[1], torch.nn.ReLU)
    assert isinstance(original.enc2[1], torch.nn.ReLU)
    assert isinstance(original.bottleneck[1], torch.nn.ReLU)
    assert isinstance(modified.enc1[1], torch.nn.LeakyReLU)
    assert (
        set(original.state_dict().keys())
        == set(modified.state_dict().keys())
    )

def test_weighted_bce_scales_positive_class():
    "Positive weighting must affect positive loss and gradient."
    logits = torch.zeros(
        (1, 1, 1, 2),
        requires_grad=True,
    )

    masks = torch.tensor(
        [[[1, 0]]],
        dtype=torch.long,
    )

    ordinary_loss = masked_bce_loss(
        logits,
        masks,
    )

    weighted_loss = masked_bce_loss(
        logits,
        masks,
        pos_weight=3.0,
    )

    assert torch.allclose(
        weighted_loss,
        ordinary_loss * 2.0,
    )

    weighted_loss.backward()
    gradient = logits.grad
    assert isinstance(
        gradient,
        torch.Tensor,
    )

    expected_gradient = torch.tensor(
        [[[[-0.75, 0.25]]]]
    )

    assert torch.allclose(
        gradient,
        expected_gradient,
    )


def test_weighted_bce_preserves_ignore_pixels():
    "Ignored pixels must contribute no gradient."
    logits = torch.tensor(
        [[[[0.0, 50.0]]]],
        requires_grad=True,
    )
    masks = torch.tensor(
        [[[1, 255]]],
        dtype=torch.long,
    )
    loss = masked_bce_loss(
        logits,
        masks,
        pos_weight=8.0,
    )
    expected_loss = torch.tensor(
        8.0 * 0.6931471805599453
    )
    assert torch.allclose(
        loss,
        expected_loss,
    )
    loss.backward()
    gradient = logits.grad
    assert isinstance(
        gradient,
        torch.Tensor,
    )
    assert gradient[0, 0, 0, 0].item() < 0.0
    assert gradient[0, 0, 0, 1].item() == 0.0