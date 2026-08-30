from shapely.geometry import Polygon
from geoai_dataset_curation.contracts import SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LabelRasterizationRequest,
    LabelVectorSource,
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


def test_label_vector_source_preserves_supervision_semantics() -> None:
    source = LabelVectorSource(
        source_id="landslide-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    assert source.source_id == "landslide-reference"
    assert source.supervision == SupervisionKind.POSITIVE_REFERENCE
    assert len(source.geometries) == 1


def test_label_rasterization_request_uses_approved_grid() -> None:
    grid = make_grid()
    source = LabelVectorSource(
        source_id="landslide-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    request = LabelRasterizationRequest(
        sources=(source,),
        grid=grid,
        output_name="label-raster",
    )
    assert request.grid is grid
    assert request.sources == (source,)
    assert request.output_name == "label-raster"