"""Create the date-only Parquet datasets consumed by the Streamlit dashboard."""

# pylint: disable=duplicate-code

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from strava_data.strava_api.processing.analytics import filter_run_data

DEFAULT_DASHBOARD_DIRECTORY = Path("data/dashboard")
ACTIVITY_COLUMNS = [
    "activity_id",
    "name",
    "activity_type",
    "distance_m",
    "moving_time_s",
    "average_speed_m_s",
    "max_speed_m_s",
    "total_elevation_gain_m",
    "activity_date",
    "average_cadence",
    "average_heartrate",
    "max_heartrate",
    "is_outdoor",
]
SPLIT_COLUMNS = [
    "split_row_id",
    "activity_id",
    "distance_m",
    "elapsed_time_s",
    "elevation_difference_m",
    "moving_time_s",
    "pace_zone",
    "split_index",
    "average_grade_adjusted_speed_m_s",
    "average_heartrate",
    "activity_date",
]
FORBIDDEN_DASHBOARD_COLUMNS = {
    "start_date",
    "start_date_local",
    "start_time",
    "timezone",
    "utc_offset",
}


def _date_only(dataframe: pd.DataFrame) -> pd.Series:
    """Return local calendar dates without retaining the source time component."""
    if "activity_date" in dataframe.columns:
        source = dataframe["activity_date"]
    elif "start_date_local" in dataframe.columns:
        source = dataframe["start_date_local"]
    else:
        return pd.Series(pd.NaT, index=dataframe.index, dtype="object")

    parsed = pd.to_datetime(source, errors="coerce")
    return parsed.dt.date


def _select_export_columns(dataframe: pd.DataFrame, requested: list[str]) -> pd.DataFrame:
    result = dataframe.copy()
    result["activity_date"] = _date_only(result)
    available = [column for column in requested if column in result.columns]
    result = result[available].copy()
    validate_dashboard_frame(result)
    return result


def validate_dashboard_frame(dataframe: pd.DataFrame) -> None:
    """Raise when a dashboard dataset contains start-time or timezone information."""
    forbidden = FORBIDDEN_DASHBOARD_COLUMNS.intersection(dataframe.columns)
    if forbidden:
        raise ValueError(f"Dashboard data contains forbidden columns: {sorted(forbidden)}")

    if "activity_date" not in dataframe.columns:
        return

    invalid = dataframe["activity_date"].dropna().map(lambda value: not isinstance(value, date))
    if invalid.any():
        raise ValueError("Dashboard activity_date values must be calendar dates only.")


def _write_parquet_atomically(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Write a Parquet file without exposing a partially written dashboard dataset."""
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    dataframe.to_parquet(temporary_path, index=False, engine="pyarrow")
    temporary_path.replace(output_path)


def export_dashboard_parquet(
    activities_df: pd.DataFrame,
    splits_df: pd.DataFrame,
    output_directory: Path | str = DEFAULT_DASHBOARD_DIRECTORY,
) -> tuple[Path, Path, Path]:
    """Write date-only activity and split Parquet files plus export metadata."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    run_activities, run_splits = filter_run_data(activities_df, splits_df)
    activities = _select_export_columns(run_activities, ACTIVITY_COLUMNS)
    splits = _select_export_columns(run_splits, SPLIT_COLUMNS)

    activities_path = output_path / "activities.parquet"
    splits_path = output_path / "splits.parquet"
    metadata_path = output_path / "metadata.json"

    _write_parquet_atomically(activities, activities_path)
    _write_parquet_atomically(splits, splits_path)

    activity_dates = activities.get("activity_date", pd.Series(dtype="object")).dropna()
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "activity_count": int(len(activities)),
        "split_count": int(len(splits)),
        "first_activity_date": (
            min(activity_dates).isoformat() if not activity_dates.empty else None
        ),
        "last_activity_date": max(activity_dates).isoformat() if not activity_dates.empty else None,
        "scope": {"activity_types": ["Run"]},
        "privacy": {
            "activity_names": "included",
            "activity_dates": "included",
            "heart_rate": "included when available",
            "precise_start_times": "removed",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return activities_path, splits_path, metadata_path
