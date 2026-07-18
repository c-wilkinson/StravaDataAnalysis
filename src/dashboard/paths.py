"""Repository paths used by the standalone dashboard."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "dashboard"
ACTIVITIES_PARQUET = DASHBOARD_DATA_DIRECTORY / "activities.parquet"
SPLITS_PARQUET = DASHBOARD_DATA_DIRECTORY / "splits.parquet"
METADATA_JSON = DASHBOARD_DATA_DIRECTORY / "metadata.json"
ASSETS_DIRECTORY = REPOSITORY_ROOT / "assets"
