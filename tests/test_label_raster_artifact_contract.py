from geoai_dataset_curation.contracts import LabelValue, SupervisionKind
from geoai_dataset_curation.image_construction.contracts import (
    AffineTransformSpec,
    RasterGridSpec,
)
from geoai_dataset_curation.label_rasterization import (
    LOOP1_LABEL_ALLOWED_VALUES,
    LabelRasterizationRequest,
    LabelVectorSource,
    create_label_raster_artifact_spec,
)
from shapely.geometry import Polygon


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


def test_loop1_allowed_values_match_label_contract() -> None:
    assert set(LOOP1_LABEL_ALLOWED_VALUES) == {
        int(LabelValue.NEGATIVE),
        int(LabelValue.POSITIVE),
        int(LabelValue.IGNORE),
    }


def test_artifact_spec_is_created_from_rasterization_request() -> None:
    grid = make_grid()
    source = LabelVectorSource(
        source_id="positive-reference",
        supervision=SupervisionKind.POSITIVE_REFERENCE,
        geometries=(make_polygon(),),
    )
    request = LabelRasterizationRequest(
        sources=(source,),
        grid=grid,
        output_name="label-raster",
    )

    spec = create_label_raster_artifact_spec(request)
    assert spec.output_name == "label-raster"
    assert spec.grid is grid
    assert spec.band_count == 1
    assert spec.dtype == "uint8"
    assert set(spec.allowed_values) == {0, 1, 255}