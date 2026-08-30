from shapely.geometry import Polygon
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterizationRequest,
    LabelVectorSource,
    validate_label_rasterization_request,
    validate_label_vector_source,
)


def make_grid() -> RasterGridSpec:
    return RasterGridSpec(
        crs="EPSG:32639",
        width=10,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=AffineTransformSpec(
            a=10.0,
            b=0.0,
            c=500000.0,
            d=0.0,
            e=-10.0,
            f=3500000.0,
        ),
    )


def make_polygon() -> Polygon:
    return Polygon(
        [
            (500000.0, 3499920.0),
            (500100.0, 3499920.0),
            (500100.0, 3500000.0),
            (500000.0, 3500000.0),
            (500000.0, 3499920.0),
        ]
    )


def test_explicit_reference_source_is_valid() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    assert validate_label_vector_source(source) == ()


def test_unlabeled_cannot_be_used_as_explicit_vector_source() -> None:
    source = LabelVectorSource(
        source_id="unlabeled",
        supervision=SupervisionKind.UNLABELED,
        geometries=(make_polygon(),),
    )
    errors = validate_label_vector_source(source)
    assert (
        "supervision must represent explicit reference evidence."
        in errors
    )


def test_nodata_cannot_be_used_as_explicit_vector_source() -> None:
    source = LabelVectorSource(
        source_id="nodata",
        supervision=SupervisionKind.NODATA,
        geometries=(make_polygon(),),
    )
    errors = validate_label_vector_source(source)
    assert (
        "supervision must represent explicit reference evidence."
        in errors
    )


def test_empty_geometry_collection_is_rejected() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(),
    )
    assert (
        "geometries must contain at least one geometry."
        in validate_label_vector_source(source)
    )


def test_duplicate_source_ids_are_rejected() -> None:
    first = LabelVectorSource(
        source_id="reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    second = LabelVectorSource(
        source_id="reference",
        supervision=SupervisionKind.NEGATIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    request = LabelRasterizationRequest(
        sources=(first, second),
        grid=make_grid(),
        output_name="label-raster",
    )
    assert (
        "source_id values must be unique."
        in validate_label_rasterization_request(request)
    )


def test_request_requires_at_least_one_source() -> None:
    request = LabelRasterizationRequest(
        sources=(),
        grid=make_grid(),
        output_name="label-raster",
    )
    assert (
        "sources must contain at least one vector source."
        in validate_label_rasterization_request(request)
    )


def test_request_requires_output_name() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    request = LabelRasterizationRequest(
        sources=(source,),
        grid=make_grid(),
        output_name=" ",
    )
    assert (
        "output_name must not be empty."
        in validate_label_rasterization_request(request)
    )


def test_request_requires_exact_grid() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    grid = RasterGridSpec(
        crs="EPSG:32639",
        width=10,
        height=8,
        pixel_size_x=10.0,
        pixel_size_y=10.0,
        transform=None,
    )
    request = LabelRasterizationRequest(
        sources=(source,),
        grid=grid,
        output_name="label-raster",
    )
    errors = validate_label_rasterization_request(request)
    assert any(
        "transform" in error
        for error in errors
    )


def test_request_accepts_loop1_rasterization_policy() -> None:
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    request = LabelRasterizationRequest(
        sources=(source,),
        grid=make_grid(),
        output_name="label-raster",
    )
    assert validate_label_rasterization_request(request) == ()