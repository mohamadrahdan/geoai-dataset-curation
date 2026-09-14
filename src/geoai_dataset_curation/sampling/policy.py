"Selected Loop 1 sampling policy"
from geoai_dataset_curation.sampling.contracts import (
    HardNegativeHandling,
    SamplingOrder,
    SamplingPolicy,
)


LOOP1_SAMPLING_POLICY = SamplingPolicy(
    select_all_eligible=True,
    exclude_all_ignore=True,
    order=SamplingOrder.CATALOG_ORDER,
    hard_negative_handling=(
        HardNegativeHandling.REQUIRE_SOURCE_PROVENANCE
    ),
)