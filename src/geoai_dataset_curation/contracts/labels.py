"Label-schema contracts for supervised segmentation"
from dataclasses import dataclass
from enum import IntEnum, StrEnum


class LabelValue(IntEnum):
    "Pixel values used by the Loop 1 training-target contract"
    NEGATIVE = 0
    POSITIVE = 1
    IGNORE = 255


class SupervisionKind(StrEnum):
    "Meaning of the evidence used to supervise one labeled area"
    POSITIVE_REFERENCE = "positive_reference"
    NEGATIVE_REFERENCE = "negative_reference"
    HARD_NEGATIVE_REFERENCE = "hard_negative_reference"
    UNLABELED = "unlabeled"
    NODATA = "nodata"


@dataclass(frozen=True)
class LabelSchemaEntry:
    "Mapping from one supervision kind to its training target"
    supervision: SupervisionKind
    target: LabelValue
    contributes_to_loss: bool


LOOP1_LABEL_SCHEMA: tuple[LabelSchemaEntry, ...] = (
    LabelSchemaEntry(
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        target=LabelValue.POSITIVE,
        contributes_to_loss=True,
    ),
    LabelSchemaEntry(
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        target=LabelValue.NEGATIVE,
        contributes_to_loss=True,
    ),
    LabelSchemaEntry(
        supervision=SupervisionKind.HARD_NEGATIVE_REFERENCE,
        target=LabelValue.NEGATIVE,
        contributes_to_loss=True,
    ),
    LabelSchemaEntry(
        supervision=SupervisionKind.UNLABELED,
        target=LabelValue.IGNORE,
        contributes_to_loss=False,
    ),
    LabelSchemaEntry(
        supervision=SupervisionKind.NODATA,
        target=LabelValue.IGNORE,
        contributes_to_loss=False,
    ),
)


def get_label_schema_entry(
    supervision: SupervisionKind,
) -> LabelSchemaEntry:
    "Return the Loop 1 schema entry for one supervision kind"
    for entry in LOOP1_LABEL_SCHEMA:
        if entry.supervision == supervision:
            return entry
    raise ValueError(
        f"Unsupported supervision kind: {supervision}"
    )