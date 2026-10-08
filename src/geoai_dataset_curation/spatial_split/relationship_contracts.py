"Spatial relationship contracts."
from dataclasses import dataclass
from enum import StrEnum


SPATIAL_RELATIONSHIP_CATALOG_SCHEMA_VERSION = "spatial-relationship-catalog-v1"
SPATIAL_LEAKAGE_GROUP_CATALOG_SCHEMA_VERSION = "spatial-leakage-group-catalog-v1"


class SpatialDistanceMetric(StrEnum):
    EUCLIDEAN_PIXEL_GAP = "euclidean_pixel_gap"


@dataclass(frozen=True)
class SpatialGroupingPolicy:
    distance_metric: SpatialDistanceMetric
    maximum_gap_pixels: int


@dataclass(frozen=True)
class SpatialTileFootprint:
    pair_id: str
    tile_id: str
    row_offset_pixels: int
    column_offset_pixels: int
    read_width_pixels: int
    read_height_pixels: int

    @property
    def row_stop_pixels(self) -> int:
        return self.row_offset_pixels + self.read_height_pixels

    @property
    def column_stop_pixels(self) -> int:
        return self.column_offset_pixels + self.read_width_pixels

    @property
    def source_pixel_count(self) -> int:
        return self.read_width_pixels * self.read_height_pixels


@dataclass(frozen=True)
class SpatialPairRelationship:
    first_pair_id: str
    first_tile_id: str
    second_pair_id: str
    second_tile_id: str
    row_overlap_pixels: int
    column_overlap_pixels: int
    row_gap_pixels: int
    column_gap_pixels: int
    linked: bool

    @property
    def shared_pixel_count(self) -> int:
        return self.row_overlap_pixels * self.column_overlap_pixels

    @property
    def gap_squared_pixels(self) -> int:
        return self.row_gap_pixels**2 + self.column_gap_pixels**2

    @property
    def overlaps_source_pixels(self) -> bool:
        return self.shared_pixel_count > 0


@dataclass(frozen=True)
class SpatialRelationshipCatalog:
    schema_version: str
    output_name: str
    pair_catalog_id: str
    tile_catalog_id: str
    grouping_policy_id: str
    footprints: tuple[SpatialTileFootprint, ...]
    relationships: tuple[SpatialPairRelationship, ...]

    @property
    def footprint_count(self) -> int:
        return len(self.footprints)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)

    @property
    def linked_relationship_count(self) -> int:
        return sum(relationship.linked for relationship in self.relationships)

    @property
    def overlapping_relationship_count(self) -> int:
        return sum(
            relationship.overlaps_source_pixels
            for relationship in self.relationships
        )


@dataclass(frozen=True)
class SpatialLeakageGroup:
    spatial_group_id: str
    pair_ids: tuple[str, ...]
    tile_ids: tuple[str, ...]

    @property
    def pair_count(self) -> int:
        return len(self.pair_ids)


@dataclass(frozen=True)
class SpatialLeakageGroupCatalog:
    schema_version: str
    output_name: str
    pair_catalog_id: str
    relationship_catalog_id: str
    grouping_policy_id: str
    groups: tuple[SpatialLeakageGroup, ...]

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def pair_count(self) -> int:
        return sum(group.pair_count for group in self.groups)

    @property
    def largest_group_size(self) -> int:
        return max((group.pair_count for group in self.groups), default=0)

    @property
    def singleton_group_count(self) -> int:
        return sum(group.pair_count == 1 for group in self.groups)