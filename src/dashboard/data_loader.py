"""Load dashboard data exclusively from the generated Parquet datasets."""

from __future__ import annotations

import json

import pandas as pd

from dashboard.paths import ACTIVITIES_PARQUET, METADATA_JSON, SPLITS_PARQUET


def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return activities, splits and metadata without accessing SQLite."""
    if not ACTIVITIES_PARQUET.exists() or not SPLITS_PARQUET.exists():
        return pd.DataFrame(), pd.DataFrame(), {}

    activities = pd.read_parquet(ACTIVITIES_PARQUET, engine="pyarrow")
    splits = pd.read_parquet(SPLITS_PARQUET, engine="pyarrow")
    for dataframe in (activities, splits):
        if "activity_date" in dataframe.columns:
            dataframe["activity_date"] = pd.to_datetime(
                dataframe["activity_date"], errors="coerce"
            ).dt.normalize()

    metadata = {}
    if METADATA_JSON.exists():
        metadata = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    return activities, splits, metadata
