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

    # Rename or create columns to match the schema in dao.py
    df = activities_df.copy()

    df["distance_m"] = df["distance"]
    df["moving_time_s"] = df["moving_time"]
    df["average_speed_m_s"] = df["average_speed"]
    df["max_speed_m_s"] = df["max_speed"]
    df["total_elevation_gain_m"] = df["total_elevation_gain"]

    # If you have a cadence column
    if "average_cadence" not in df.columns:
        df["average_cadence"] = 0.0

    df["start_date_local"] = df["start_date_local"]

    # Convert type to "Run", "Ride", etc., if needed
    # df["activity_type"] = np.where(df["type"].str.lower() == "run", "Run", df["type"])

    # Keep only relevant columns for DB insertion
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
        "average_cadence"
    ]

    # Return with matching column names
    return df[final_cols].copy()


def transform_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches splits data from Strava activities.

    :param splits_df: DataFrame from activity detail calls.
    :return: DataFrame with standardized columns for splits.
    """
    if splits_df.empty:
        return pd.DataFrame()

    df = splits_df.copy()

    df["distance_m"] = df["distance"]
    df["elapsed_time_s"] = df["elapsed_time"]
    df["elevation_difference_m"] = df["elevation_difference"]
    df["moving_time_s"] = df["moving_time"]
    df["average_grade_adjusted_speed_m_s"] = df["average_grade_adjusted_speed"]
    df["average_heartrate"] = df.get("average_heartrate", np.nan)
    df["split_index"] = df["split"]
    df["start_date_local"] = df["start_date_local"]

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
        "start_date_local"
    ]

    # Filter only ~1 km splits if that is desired
    # df = df[(df["distance_m"] > 950) & (df["distance_m"] < 1050)]

    return df[final_cols].copy()
