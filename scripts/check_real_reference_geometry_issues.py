"Inspect geometry-validity issues in real private reference vectors"
import os
from pathlib import Path
import geopandas as gpd
from shapely.validation import explain_validity


REFERENCE_PATHS = {
    "positive-reference": "GEOAI_POSITIVE_REFERENCE_PATH",
    "negative-reference": "GEOAI_NEGATIVE_REFERENCE_PATH",
    "hard-negative-reference": "GEOAI_HARD_NEGATIVE_REFERENCE_PATH",
}


def main() -> int:
    total_invalid = 0
    for source_id, env_name in REFERENCE_PATHS.items():
        value = os.getenv(env_name)
        if value is None or not value.strip():
            raise ValueError(
                f"Required environment variable is missing: {env_name}"
            )
        path = Path(value)
        frame = gpd.read_file(path)
        invalid = frame.loc[
            ~frame.geometry.is_valid
        ]
        print()
        print(source_id)
        print("=" * len(source_id))
        print(f"Path: {path}")
        print(f"Feature count: {len(frame)}")
        print(f"CRS: {frame.crs}")
        print(f"Invalid geometries: {len(invalid)}")
        for index, geometry in invalid.geometry.items():
            print(
                f"  feature={index}: "
                f"{explain_validity(geometry)}"
            )

        total_invalid += len(invalid)
    print()
    print(f"Total invalid geometries: {total_invalid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )