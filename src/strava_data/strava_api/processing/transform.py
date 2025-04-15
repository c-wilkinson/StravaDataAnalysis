"""
Data transformation utilities for activities and splits.
"""

import pandas as pd
import numpy as np


def transform_activities(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches raw Strava activities.

    :param activities_df: Raw DataFrame from Strava's /activities endpoint.
    :return: DataFrame with standardized columns and transformations.
    """
    if activities_df.empty:
        return pd.DataFrame()

    activities_clean = activities_df.copy()

    activities_clean["distance_m"] = activities_clean["distance"]
    activities_clean["moving_time_s"] = activities_clean["moving_time"]
    activities_clean["average_speed_m_s"] = activities_clean["average_speed"]
    activities_clean["max_speed_m_s"] = activities_clean["max_speed"]
    activities_clean["total_elevation_gain_m"] = activities_clean["total_elevation_gain"]

    if "average_cadence" not in activities_clean.columns:
        activities_clean["average_cadence"] = 0.0

    activities_clean["start_date_local"] = activities_clean["start_date_local"]
    activities_clean["activity_type"] = np.where(
        activities_clean["type"].str.lower() == "run", "Run", activities_clean["type"]
    )

    final_cols = [
        "id",
        "name",
        "type",
        "distance_m",
        "moving_time_s",
        "average_speed_m_s",
        "max_speed_m_s",
        "total_elevation_gain_m",
        "start_date_local",
        "average_cadence",
    ]

    return activities_clean[final_cols].copy()


def transform_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches splits data from Strava activities.

    :param splits_df: DataFrame from activity detail calls.
    :return: DataFrame with standardized columns for splits.
    """
    if splits_df.empty:
        return pd.DataFrame()

    splits_clean = splits_df.copy()

    splits_clean["distance_m"] = splits_clean["distance"]
    splits_clean["elapsed_time_s"] = splits_clean["elapsed_time"]
    splits_clean["elevation_difference_m"] = splits_clean["elevation_difference"]
    splits_clean["moving_time_s"] = splits_clean["moving_time"]
    splits_clean["average_grade_adjusted_speed_m_s"] = splits_clean["average_grade_adjusted_speed"]
    splits_clean["average_heartrate"] = splits_clean.get("average_heartrate", np.nan)
    splits_clean["split_index"] = splits_clean["split"]
    splits_clean["start_date_local"] = splits_clean["start_date_local"]

    final_cols = [
        "activity_id",
        "distance_m",
        "elapsed_time_s",
        "elevation_difference_m",
        "moving_time_s",
        "pace_zone",
        "split_index",
        "average_grade_adjusted_speed_m_s",
        "average_heartrate",
        "start_date_local",
    ]

    return splits_clean[final_cols].copy()
