"""
Utilities for chart styling or other shared visualisation helpers.
"""

import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DOB = datetime.datetime(1985, 1, 26)


def configure_matplotlib_styles() -> None:
    """
    Applies consistent style settings across all charts.
    """
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["legend.fontsize"] = 12
    plt.rcParams["axes.grid"] = True


def format_pace(value: float, _) -> str:
    """
    Converts a time value in seconds into 'minutes:seconds' format.
    """
    if not np.isfinite(value):
        return ""
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes}:{seconds:02d}"


def classify_zone_dynamic(heart_rate: float, date_str: str) -> str:
    """
    Classifies heart rate into a dynamic training zone based on age at the run date.
    """
    try:
        run_date = pd.to_datetime(date_str)
    except (ValueError, TypeError):
        return "Unknown"

    age = run_date.year - DOB.year - ((run_date.month, run_date.day) < (DOB.month, DOB.day))
    max_hr = 220 - age
    heart_pct = heart_rate / max_hr

    if heart_pct < 0.60:
        return "Z1 (<60%)"
    if heart_pct < 0.70:
        return "Z2 (60–70%)"
    if heart_pct < 0.80:
        return "Z3 (70–80%)"
    if heart_pct < 0.90:
        return "Z4 (80–90%)"
    return "Z5 (90–100%)"


def prepare_pace_distance_data(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates and derives per-run pace metrics from individual split data.
    """
    splits = splits_df.copy()
    splits["pace_sec_km"] = splits["elapsed_time_s"] / (splits["distance_m"] / 1000)
    grouped_df = (
        splits.groupby(["activity_id", "start_date_local"])
        .agg({"distance_m": "sum", "elapsed_time_s": "sum"})
        .reset_index()
    )
    grouped_df["pace_sec_km"] = grouped_df["elapsed_time_s"] / (grouped_df["distance_m"] / 1000)
    grouped_df["distance_km"] = grouped_df["distance_m"] / 1000
    grouped_df["pace_sec"] = grouped_df["pace_sec_km"]
    grouped_df["year"] = pd.to_datetime(grouped_df["start_date_local"]).dt.year
    return grouped_df


def prepare_time_distance_data(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches raw activities data for plotting time vs. distance trends.
    """
    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[data["distance_km"] >= 0.5]
    data["time_seconds"] = data["moving_time_s"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    last_run_date = pd.to_datetime(data["start_date_local"]).max()
    data["is_last_run"] = pd.to_datetime(data["start_date_local"]) == last_run_date
    return data


def calculate_decay_point(data: pd.DataFrame) -> tuple[float, float]:
    """
    Computes an extrapolated decay point for visualizing projected pacing trends.
    """
    max_distance = data["distance_km"].max()
    max_time = data["time_seconds"].max()
    decay_distance = max_distance + 2
    average_pace = max_time / max_distance
    decay_time = decay_distance * (average_pace + 180)
    return decay_distance, decay_time
