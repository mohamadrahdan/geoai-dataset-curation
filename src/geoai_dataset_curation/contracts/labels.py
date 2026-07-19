"Label values used by the initial landslide-segmentation contract"

from enum import IntEnum


class LabelValue(IntEnum):
    "Supported pixel-label values for Loop 1"

    BACKGROUND = 0
    LANDSLIDE = 1
    IGNORE = 255