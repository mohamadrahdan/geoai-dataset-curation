"Small four-band U-Net and ignore-aware binary segmentation loss."
import math
import torch
from torch import nn
from torch.nn import functional as F


class DoubleConv(nn.Sequential):
    "Two 3x3 convolutions with the selected activation."
    def __init__(
        self,
        input_channels: int,
        output_channels: int,
        activation: str = "relu",
    ) -> None:
        if activation == "relu":
            activation1 = nn.ReLU(inplace=True)
            activation2 = nn.ReLU(inplace=True)

        elif activation == "leaky_relu":
            activation1 = nn.LeakyReLU(
                negative_slope=0.1,
                inplace=True,
            )
            activation2 = nn.LeakyReLU(
                negative_slope=0.1,
                inplace=True,
            )

        else:
            raise ValueError(
                f"Unsupported activation: {activation}"
            )

        super().__init__(
            nn.Conv2d(
                input_channels,
                output_channels,
                kernel_size=3,
                padding=1,
            ),
            activation1,
            nn.Conv2d(
                output_channels,
                output_channels,
                kernel_size=3,
                padding=1,
            ),
            activation2,
        )


class SmallUNet(nn.Module):
    "Small U-Net with four input channels and one output logit."
    def __init__(
        self,
        in_channels: int = 4,
        base_channels: int = 8,
        activation: str = "relu",
    ) -> None:
        super().__init__()

        self.enc1 = DoubleConv(
            in_channels,
            base_channels,
            activation,
        )

        self.enc2 = DoubleConv(
            base_channels,
            base_channels * 2,
            activation,
        )

        self.bottleneck = DoubleConv(
            base_channels * 2,
            base_channels * 4,
            activation,
        )

        self.dec2 = DoubleConv(
            base_channels * 6,
            base_channels * 2,
            activation,
        )

        self.dec1 = DoubleConv(
            base_channels * 3,
            base_channels,
            activation,
        )

        self.out = nn.Conv2d(
            base_channels,
            1,
            kernel_size=1,
        )

    def forward(
        self,
        images: torch.Tensor,
    ) -> torch.Tensor:
        if images.ndim != 4 or images.shape[1] != 4:
            raise ValueError("Expected images in [batch, 4, height, width] format.")

        if min(images.shape[-2:]) < 4:
            raise ValueError("Image height and width must both be at least 4.")

        # Encoder
        skip1 = self.enc1(images)
        skip2 = self.enc2(
            F.max_pool2d(skip1, 2)
        )

        # Bottleneck
        hidden = self.bottleneck(
            F.max_pool2d(skip2, 2)
        )

        # Decoder: stage 2
        up2 = F.interpolate(
            hidden,
            size=skip2.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )
        up2 = self.dec2(
            torch.cat([up2, skip2], dim=1)
        )

        # Decoder: stage 1
        up1 = F.interpolate(
            up2,
            size=skip1.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )
        up1 = self.dec1(
            torch.cat([up1, skip1], dim=1)
        )
        return self.out(up1)


def masked_bce_loss(
    logits: torch.Tensor,
    masks: torch.Tensor,
    pos_weight: float = 1.0,
) -> torch.Tensor:
    """Compute binary BCE on supervised pixels only.
    Expected:
        logits: [B, 1, H, W]
        masks:  [B, H, W]
    Label semantics:
        0   = verified negative
        1   = landslide
        255 = ignore / unlabeled

    pos_weight:
        1.0 = original unweighted BCE
        >1  = increased penalty for positive-class errors
    """

    if logits.ndim != 4 or logits.shape[1] != 1:
        raise ValueError("Expected logits shaped [B, 1, H, W].")

    if masks.shape != (
        logits.shape[0],
        *logits.shape[2:],
    ):
        raise ValueError("Mask dimensions do not match logits.")

    if not torch.all(
        (masks == 0)
        | (masks == 1)
        | (masks == 255)
    ).item():
        raise ValueError("Mask values must be 0, 1, or 255.")

    if not math.isfinite(pos_weight) or pos_weight <= 0:
        raise ValueError("pos_weight must be finite and greater than zero.")

    valid = masks != 255

    if not valid.any().item():
        raise ValueError("Batch contains no supervised pixels.")

    targets = torch.where(
        valid,
        masks,
        0,
    )

    targets = targets.to(
        logits.dtype
    ).unsqueeze(1)

    positive_weight_tensor = torch.tensor(
        pos_weight,
        dtype=logits.dtype,
        device=logits.device,
    )

    pixel_loss = F.binary_cross_entropy_with_logits(
        logits,
        targets,
        pos_weight=positive_weight_tensor,
        reduction="none",
    )

    return pixel_loss.masked_select(
        valid.unsqueeze(1)
    ).mean()