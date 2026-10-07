"Visual-review contact sheets for image-mask pairs"
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import rasterio
from geoai_dataset_curation.sampling import (
    ImageMaskPairCatalog,
    ImageMaskPairRecord,
)


DEFAULT_RGB_BAND_INDICES = (3, 2, 1)
DEFAULT_TILE_SIZE = 256
DEFAULT_PAIRS_PER_PAGE = 5


def _stretch_rgb(
    bands: np.ndarray,
) -> np.ndarray:
    "Apply an independent percentile stretch to three bands"
    rgb = np.moveaxis(
        bands.astype(np.float64, copy=False),
        0,
        -1,
    )
    stretched = np.zeros(
        rgb.shape,
        dtype=np.uint8,
    )

    for channel_index in range(3):
        channel = rgb[:, :, channel_index]
        finite_mask = np.isfinite(channel)
        finite_values = channel[finite_mask]

        if finite_values.size == 0:
            continue

        lower, upper = np.percentile(
            finite_values,
            (2.0, 98.0),
        )

        if upper <= lower:
            continue

        normalized = (
            channel - lower
        ) / (
            upper - lower
        )
        normalized = np.clip(
            normalized,
            0.0,
            1.0,
        )
        normalized[~finite_mask] = 0.0
        stretched[:, :, channel_index] = (
            normalized * 255.0
        ).astype(np.uint8)

    return stretched


def _colorize_mask(mask: np.ndarray) -> np.ndarray:
    "Render positive, negative, and ignore mask values"
    colored = np.zeros(
        (*mask.shape, 3),
        dtype=np.uint8,
    )
    colored[mask == 255] = (40, 40, 40)
    colored[mask == 0] = (0, 180, 255)
    colored[mask == 1] = (255, 0, 0)
    return colored


def _build_overlay(
    rgb: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    "Overlay supervised mask pixels on an RGB image"
    overlay = rgb.astype(
        np.float32,
        copy=True,
    )

    negative_pixels = mask == 0
    positive_pixels = mask == 1

    overlay[negative_pixels] = (
        0.70 * overlay[negative_pixels]
        + 0.30 * np.array(
            [0, 180, 255],
            dtype=np.float32,
        )
    )
    overlay[positive_pixels] = (
        0.40 * overlay[positive_pixels]
        + 0.60 * np.array(
            [255, 0, 0],
            dtype=np.float32,
        )
    )

    return np.clip(
        overlay,
        0.0,
        255.0,
    ).astype(np.uint8)


def _load_review_images(
    pair: ImageMaskPairRecord,
    *,
    rgb_band_indices: tuple[int, int, int],
    tile_size: int,
) -> tuple[Image.Image, Image.Image, Image.Image]:
    "Load and render image, mask, and overlay views"

    with rasterio.open(pair.image_tile_path) as image_dataset:
        if max(rgb_band_indices) > image_dataset.count:
            raise ValueError("rgb_band_indices exceed the image band count.")

        image_bands = image_dataset.read(
            rgb_band_indices
        )

    with rasterio.open(pair.mask_tile_path) as mask_dataset:
        mask = mask_dataset.read(1)

    if image_bands.shape[1:] != mask.shape:
        raise ValueError("Image and mask shapes must match for visual review.")

    rgb = _stretch_rgb(image_bands)
    colored_mask = _colorize_mask(mask)
    overlay = _build_overlay(rgb, mask)

    output_size = (tile_size, tile_size)

    image_view = Image.fromarray(
        rgb,
        mode="RGB",
    ).resize(
        output_size,
        Image.Resampling.BILINEAR,
    )
    mask_view = Image.fromarray(
        colored_mask,
        mode="RGB",
    ).resize(
        output_size,
        Image.Resampling.NEAREST,
    )
    overlay_view = Image.fromarray(
        overlay,
        mode="RGB",
    ).resize(
        output_size,
        Image.Resampling.BILINEAR,
    )

    return image_view, mask_view, overlay_view


def _short_id(value: str) -> str:
    "Return a short human-readable identity"
    return value.removeprefix("sha256:")[:12]


def generate_pair_contact_sheets(
    pair_catalog: ImageMaskPairCatalog,
    *,
    output_directory: Path,
    rgb_band_indices: tuple[int, int, int] = (
        DEFAULT_RGB_BAND_INDICES
    ),
    tile_size: int = DEFAULT_TILE_SIZE,
    pairs_per_page: int = DEFAULT_PAIRS_PER_PAGE,
) -> tuple[Path, ...]:
    "Generate deterministic visual-review contact sheets"
    if len(rgb_band_indices) != 3:
        raise ValueError("rgb_band_indices must contain three bands.")

    if min(rgb_band_indices) < 1:
        raise ValueError("rgb_band_indices must use one-based indices.")

    if tile_size <= 0:
        raise ValueError("tile_size must be positive.")

    if pairs_per_page <= 0:
        raise ValueError("pairs_per_page must be positive.")

    if not pair_catalog.pairs:
        raise ValueError("pair_catalog must contain at least one pair.")

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_pages = tuple(
        output_directory.glob("contact_sheet_*.png")
    )
    if existing_pages:
        raise FileExistsError("Output directory already contains contact sheets.")

    margin = 12
    gap = 8
    page_header_height = 28
    row_label_height = 24
    row_gap = 12
    row_height = row_label_height + tile_size
    page_width = (
        2 * margin
        + 3 * tile_size
        + 2 * gap
    )

    page_paths: list[Path] = []

    for page_offset in range(
        0,
        pair_catalog.pair_count,
        pairs_per_page,
    ):
        page_pairs = pair_catalog.pairs[
            page_offset:
            page_offset + pairs_per_page
        ]
        page_height = (
            2 * margin
            + page_header_height
            + len(page_pairs) * row_height
            + max(0, len(page_pairs) - 1) * row_gap
        )

        page = Image.new(
            "RGB",
            (page_width, page_height),
            color="white",
        )
        draw = ImageDraw.Draw(page)

        column_x = (
            margin,
            margin + tile_size + gap,
            margin + 2 * (tile_size + gap),
        )
        column_labels = (
            "IMAGE",
            "MASK",
            "OVERLAY",
        )

        for x, label in zip(
            column_x,
            column_labels,
            strict=True,
        ):
            draw.text(
                (x, margin),
                label,
                fill="black",
            )

        row_y = margin + page_header_height

        for pair in page_pairs:
            image_view, mask_view, overlay_view = (
                _load_review_images(
                    pair,
                    rgb_band_indices=rgb_band_indices,
                    tile_size=tile_size,
                )
            )

            label = (
                f"tile={_short_id(pair.tile_id)}  "
                f"class={pair.label_class.value}  "
                "negative="
                f"{pair.negative_provenance_kind.value}"
            )
            draw.text(
                (margin, row_y),
                label,
                fill="black",
            )

            image_y = row_y + row_label_height
            page.paste(
                image_view,
                (column_x[0], image_y),
            )
            page.paste(
                mask_view,
                (column_x[1], image_y),
            )
            page.paste(
                overlay_view,
                (column_x[2], image_y),
            )

            row_y += row_height + row_gap

        page_number = (
            page_offset // pairs_per_page
        ) + 1
        page_path = (
            output_directory
            / f"contact_sheet_{page_number:03d}.png"
        )
        page.save(
            page_path,
            format="PNG",
        )
        page_paths.append(page_path)

    return tuple(page_paths)