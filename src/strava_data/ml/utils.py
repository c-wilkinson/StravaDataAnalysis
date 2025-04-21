"""
Shared utilities for machine learning feature engineering.
"""

import pandas as pd


def prepare_pace_summary(splits_df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """
    Aggregates pace-based metrics by the given group columns (e.g. weekly or per run).
    """
    data = splits_df.copy()
    data = data[(data["distance_m"] >= 950) & (data["distance_m"] <= 1050)]
    data["pace_sec_km"] = data["elapsed_time_s"] / (data["distance_m"] / 1000)
    data["distance_km"] = data["distance_m"] / 1000

    grouped = (
        data.groupby(group_cols)
        .agg(
            distance_km=("distance_km", "sum"),
            pace_median=("pace_sec_km", "median"),
            pace_std=("pace_sec_km", "std"),
            split_count=("pace_sec_km", "count"),
        )
        .reset_index()
        .dropna()
    )

    return grouped
