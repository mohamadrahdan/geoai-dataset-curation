import pytest
from shapely.geometry import box
from geoai_dataset_curation.contracts.labels import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelVectorSource,
    analyze_source_spatial_qc,
    validate_no_disjoint_geometries,
)
from geoai_dataset_curation.label_rasterization.spatial_qc import compute_source_overlap_pixel_count


GRID = RasterGridSpec(
    crs="EPSG:32639",
    width=4,
    height=4,
    pixel_size_x=10.0,
    pixel_size_y=10.0,
    transform=AffineTransformSpec(
        a=10.0,
        b=0.0,
        c=0.0,
        d=0.0,
        e=-10.0,
        f=40.0,
    ),
)


def test_spatial_qc_reports_inside_feature_pixels() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(
            box(0.0, 30.0, 10.0, 40.0),
        ),
    )
    result = analyze_source_spatial_qc(
        source,
        GRID,
    )
    assert result.feature_count == 1
    assert result.covered_pixel_count == 1
    assert result.zero_pixel_feature_count == 0
    assert result.partially_outside_feature_count == 0
    assert result.disjoint_feature_count == 0


def test_spatial_qc_reports_disjoint_feature() -> None:
    source = LabelVectorSource(
        source_id="negative-reference",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(
            box(100.0, 100.0, 110.0, 110.0),
        ),
    )
    result = analyze_source_spatial_qc(
        source,
        GRID,
    )
    assert result.disjoint_feature_count == 1
    assert result.zero_pixel_feature_count == 1


def test_disjoint_geometry_is_rejected_by_policy_gate() -> None:
    source = LabelVectorSource(
        source_id="negative-reference",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(
            box(100.0, 100.0, 110.0, 110.0),
        ),
    )

    with pytest.raises(
        ValueError,
        match="fully outside the target grid",
    ):
        validate_no_disjoint_geometries(
            source,
            GRID,
        )


def test_source_overlap_counts_shared_pixels() -> None:
    first = LabelVectorSource(
        source_id="negative-reference",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(
            box(0.0, 30.0, 20.0, 40.0),
        ),
    )
    second = LabelVectorSource(
        source_id="hard-negative-reference",
        supervision=SupervisionKind.HARD_NEGATIVE_REFERENCE,
        geometries=(
            box(10.0, 30.0, 30.0, 40.0),
        ),
    )
    result = compute_source_overlap_pixel_count(
        first,
        second,
        GRID,
    )
    assert result == 1