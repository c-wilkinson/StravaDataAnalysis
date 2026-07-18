"""Reusable data preparation and aggregation for static and interactive charts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strava_data.strava_api.visualisation.utils import classify_zone_dynamic

ACTIVITY_DATE_COLUMNS = ("activity_date", "start_date_local")


def _resolve_date_column(dataframe: pd.DataFrame) -> str:
    """Return the first supported activity date column."""
    for column in ACTIVITY_DATE_COLUMNS:
        if column in dataframe.columns:
            return column
    raise ValueError("Data must contain activity_date or start_date_local.")


def filter_run_data(
    activities_df: pd.DataFrame, splits_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return running activities and only the splits belonging to those runs."""
    activities = activities_df.copy()
    splits = splits_df.copy()

    if activities.empty or "activity_type" not in activities.columns:
        return activities, splits

    activity_types = activities["activity_type"].astype("string").str.strip().str.casefold()
    activities = activities.loc[activity_types.eq("run")].copy()

    if "activity_id" not in activities.columns or "activity_id" not in splits.columns:
        return activities, splits

    activity_ids = activities["activity_id"]
    splits = splits.loc[splits["activity_id"].isin(activity_ids)].copy()
    return activities, splits


def prepare_activities(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return activities with consistent date, distance, pace and duration columns."""
    if activities_df.empty:
        return pd.DataFrame()

    data = activities_df.copy()
    date_column = _resolve_date_column(data)
    data["activity_date"] = pd.to_datetime(data[date_column], errors="coerce").dt.normalize()
    data = data.dropna(subset=["activity_date"])

    numeric_defaults = {
        "distance_m": 0.0,
        "moving_time_s": 0.0,
        "average_speed_m_s": 0.0,
        "max_speed_m_s": 0.0,
        "total_elevation_gain_m": 0.0,
        "average_cadence": 0.0,
        "average_heartrate": float("nan"),
        "max_heartrate": float("nan"),
    }
    for column, default in numeric_defaults.items():
        if column not in data.columns:
            data[column] = default
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if pd.notna(default):
            data[column] = data[column].fillna(default)

    data["distance_km"] = data["distance_m"] / 1000.0
    data["moving_time_hours"] = data["moving_time_s"] / 3600.0
    valid_distance = data["distance_km"].where(data["distance_km"] > 0)
    data["pace_sec_km"] = data["moving_time_s"].div(valid_distance)
    data["year"] = data["activity_date"].dt.year
    data["month"] = data["activity_date"].dt.month
    data["month_start"] = data["activity_date"].dt.to_period("M").dt.to_timestamp()
    data["weekday"] = data["activity_date"].dt.day_name()

    if "name" not in data.columns:
        data["name"] = "Activity"
    if "activity_type" not in data.columns:
        data["activity_type"] = "Run"
    if "is_outdoor" not in data.columns:
        data["is_outdoor"] = 1

    return data.sort_values("activity_date").reset_index(drop=True)


def prepare_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return splits with consistent date, distance, pace and heart-rate columns."""
    if splits_df.empty:
        return pd.DataFrame()

    data = splits_df.copy()
    date_column = _resolve_date_column(data)
    data["activity_date"] = pd.to_datetime(data[date_column], errors="coerce").dt.normalize()
    data = data.dropna(subset=["activity_date"])

    numeric_defaults = {
        "distance_m": 0.0,
        "elapsed_time_s": 0.0,
        "moving_time_s": 0.0,
        "elevation_difference_m": 0.0,
        "average_heartrate": float("nan"),
        "average_grade_adjusted_speed_m_s": 0.0,
        "split_index": 0,
    }
    for column, default in numeric_defaults.items():
        if column not in data.columns:
            data[column] = default
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if pd.notna(default):
            data[column] = data[column].fillna(default)

    data["distance_km"] = data["distance_m"] / 1000.0
    valid_distance = data["distance_km"].where(data["distance_km"] > 0)
    data["pace_sec_km"] = data["elapsed_time_s"].div(valid_distance)
    data["year"] = data["activity_date"].dt.year
    data["month"] = data["activity_date"].dt.month
    data["month_start"] = data["activity_date"].dt.to_period("M").dt.to_timestamp()
    data["weekday"] = data["activity_date"].dt.day_name()
    sort_columns = ["activity_date", "activity_id", "split_index"]
    return data.sort_values(sort_columns).reset_index(drop=True)


def activity_heart_rate_summary(
    activities_df: pd.DataFrame, splits_df: pd.DataFrame
) -> pd.DataFrame:
    """Fill missing activity heart-rate values from the available split data.

    Older database rows predate the activity-level heart-rate columns. Their
    average is weighted by split moving time, while their fallback maximum is
    the highest split average because instantaneous maximum heart rate is not
    present in the split dataset.
    """
    activities = prepare_activities(activities_df)
    if activities.empty:
        return activities

    activities["average_heartrate_from_splits"] = False
    activities["max_heartrate_from_splits"] = False
    if "activity_id" not in activities.columns:
        return activities

    splits = prepare_splits(splits_df)
    if splits.empty or "activity_id" not in splits.columns:
        return activities

    valid_splits = splits.loc[
        splits["average_heartrate"].between(30.0, 250.0, inclusive="both")
    ].copy()
    if valid_splits.empty:
        return activities

    valid_splits["heart_rate_weight_s"] = valid_splits["moving_time_s"].where(
        valid_splits["moving_time_s"] > 0, valid_splits["elapsed_time_s"]
    )
    valid_splits["heart_rate_weight_s"] = valid_splits["heart_rate_weight_s"].where(
        valid_splits["heart_rate_weight_s"] > 0, 1.0
    )
    valid_splits["weighted_heartrate"] = (
        valid_splits["average_heartrate"] * valid_splits["heart_rate_weight_s"]
    )

    split_summary = valid_splits.groupby("activity_id", as_index=False).agg(
        weighted_heartrate=("weighted_heartrate", "sum"),
        heart_rate_weight_s=("heart_rate_weight_s", "sum"),
        split_max_heartrate=("average_heartrate", "max"),
    )
    split_summary["split_average_heartrate"] = (
        split_summary["weighted_heartrate"] / split_summary["heart_rate_weight_s"]
    )

    activities = activities.merge(
        split_summary[["activity_id", "split_average_heartrate", "split_max_heartrate"]],
        on="activity_id",
        how="left",
    )
    missing_average = activities["average_heartrate"].isna() | activities["average_heartrate"].le(0)
    missing_maximum = activities["max_heartrate"].isna() | activities["max_heartrate"].le(0)

    activities["average_heartrate_from_splits"] = (
        missing_average & activities["split_average_heartrate"].notna()
    )
    activities["max_heartrate_from_splits"] = (
        missing_maximum & activities["split_max_heartrate"].notna()
    )
    activities["average_heartrate"] = activities["average_heartrate"].where(
        ~missing_average, activities["split_average_heartrate"]
    )
    activities["max_heartrate"] = activities["max_heartrate"].where(
        ~missing_maximum, activities["split_max_heartrate"]
    )
    return activities.drop(
        columns=["split_average_heartrate", "split_max_heartrate"], errors="ignore"
    )


def one_kilometre_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Filter prepared split data to splits between 950 m and 1,050 m."""
    data = prepare_splits(splits_df)
    if data.empty:
        return data
    return data[data["distance_km"].between(0.95, 1.05)].copy()


def monthly_distance(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total distance by month and year."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    return (
        data.groupby(["year", "month", "month_start"], as_index=False)["distance_km"]
        .sum()
        .sort_values("month_start")
    )


def cumulative_distance(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return cumulative distance over time."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    daily = data.groupby("activity_date", as_index=False)["distance_km"].sum()
    daily["cumulative_distance_km"] = daily["distance_km"].cumsum()
    return daily


def rolling_distance(activities_df: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """Return calendar-day rolling distance totals."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    daily = data.groupby("activity_date")["distance_km"].sum().sort_index()
    complete_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(complete_index, fill_value=0.0)
    result = daily.rolling(window_days, min_periods=1).sum().rename("rolling_distance_km")
    return result.rename_axis("activity_date").reset_index()


def longest_run_by_month(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return the longest activity in each calendar month."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    index = data.groupby("month_start")["distance_km"].idxmax()
    columns = ["month_start", "activity_date", "name", "distance_km"]
    return data.loc[index, columns].sort_values("month_start").reset_index(drop=True)


def pace_over_time(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return valid approximately one-kilometre split paces."""
    data = one_kilometre_splits(splits_df)
    if data.empty:
        return data
    valid = np.isfinite(data["pace_sec_km"]) & data["pace_sec_km"].between(120, 1200)
    return data[valid].copy()


def monthly_pace(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return fastest and median one-kilometre pace by month."""
    data = pace_over_time(splits_df)
    if data.empty:
        return data
    return (
        data.groupby(["year", "month", "month_start"], as_index=False)
        .agg(
            fastest_pace_sec_km=("pace_sec_km", "min"),
            median_pace_sec_km=("pace_sec_km", "median"),
        )
        .sort_values("month_start")
    )


def pace_variability(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return pace standard deviation for activities with at least three valid splits."""
    data = pace_over_time(splits_df)
    if data.empty:
        return data
    grouped = data.groupby(["activity_id", "activity_date"], as_index=False).agg(
        pace_std_sec_km=("pace_sec_km", "std"),
        split_count=("pace_sec_km", "count"),
    )
    return grouped[grouped["split_count"] >= 3].sort_values("activity_date")


def monthly_elevation_per_km(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly elevation gain per kilometre."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    grouped = data.groupby(["year", "month", "month_start"], as_index=False).agg(
        distance_km=("distance_km", "sum"),
        elevation_m=("total_elevation_gain_m", "sum"),
    )
    grouped = grouped[grouped["distance_km"] > 0].copy()
    grouped["elevation_per_km"] = grouped["elevation_m"] / grouped["distance_km"]
    return grouped.sort_values("month_start")


def training_load(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return the project's existing effort score and rolling seven-activity average."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    data["effort_score"] = (data["distance_km"] * 10.0) + (data["total_elevation_gain_m"] * 1.5)
    data["rolling_effort"] = data["effort_score"].rolling(window=7, min_periods=1).mean()
    return data


def monthly_vo2_proxy(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return the existing fastest-split VO2-style proxy by month."""
    data = pace_over_time(splits_df)
    if data.empty:
        return data
    data["speed_mps"] = data["distance_m"] / data["elapsed_time_s"]
    data["vo2_proxy"] = 15.0 * data["speed_mps"]
    return (
        data.groupby(["year", "month", "month_start"], as_index=False)["vo2_proxy"]
        .max()
        .sort_values("month_start")
    )


def heart_rate_zones(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Return minutes spent in dynamic heart-rate zones by month."""
    data = prepare_splits(splits_df)
    if data.empty:
        return pd.DataFrame()
    data = data.dropna(subset=["average_heartrate"]).copy()
    if data.empty:
        return data
    data["heart_rate_zone"] = data.apply(
        lambda row: classify_zone_dynamic(row["average_heartrate"], row["activity_date"]),
        axis=1,
    )
    data["time_minutes"] = data["elapsed_time_s"] / 60.0
    return (
        data.groupby(["month_start", "heart_rate_zone"], as_index=False)["time_minutes"]
        .sum()
        .sort_values("month_start")
    )


def run_rest_summary(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Return run days, rest days and run-day ratio by month."""
    data = prepare_activities(activities_df)
    if data.empty:
        return data
    run_dates = data[["activity_date"]].drop_duplicates().assign(ran=1)
    dates = pd.DataFrame(
        {"activity_date": pd.date_range(data["activity_date"].min(), data["activity_date"].max())}
    )
    dates = dates.merge(run_dates, on="activity_date", how="left").fillna({"ran": 0})
    dates["year"] = dates["activity_date"].dt.year
    dates["month"] = dates["activity_date"].dt.month
    summary = dates.groupby(["year", "month"], as_index=False).agg(
        run_days=("ran", "sum"),
        calendar_days=("ran", "size"),
    )
    summary["rest_days"] = summary["calendar_days"] - summary["run_days"]
    summary["run_day_ratio"] = summary["run_days"] / summary["calendar_days"]
    return summary
