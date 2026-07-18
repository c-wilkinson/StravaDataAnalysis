"""Tests for the dashboard-safe Parquet export."""

import json
from datetime import date

import pandas as pd
from pyarrow import parquet

from strava_data.db.parquet import (
    FORBIDDEN_DASHBOARD_COLUMNS,
    export_dashboard_parquet,
)


def test_export_retains_date_name_and_heart_rate_without_start_time(tmp_path):
    """The export keeps useful fields but removes precise time information."""
    activities = pd.DataFrame(
        {
            "activity_id": [101],
            "name": ["Evening Run"],
            "activity_type": ["Run"],
            "distance_m": [5000.0],
            "moving_time_s": [1500],
            "average_speed_m_s": [3.33],
            "max_speed_m_s": [4.2],
            "total_elevation_gain_m": [42.0],
            "start_date_local": ["2026-07-18T18:34:21"],
            "average_cadence": [172.0],
            "average_heartrate": [151.0],
            "max_heartrate": [174.0],
            "is_outdoor": [1],
            "timezone": ["Europe/London"],
            "utc_offset": [3600],
        }
    )
    splits = pd.DataFrame(
        {
            "split_row_id": [1],
            "activity_id": [101],
            "distance_m": [1000.0],
            "elapsed_time_s": [300],
            "elevation_difference_m": [4.0],
            "moving_time_s": [298],
            "pace_zone": [2],
            "split_index": [1],
            "average_grade_adjusted_speed_m_s": [3.4],
            "average_heartrate": [149.0],
            "start_date_local": ["2026-07-18T18:34:21"],
        }
    )

    activities_path, splits_path, metadata_path = export_dashboard_parquet(
        activities, splits, tmp_path
    )

    exported_activities = pd.read_parquet(activities_path)
    exported_splits = pd.read_parquet(splits_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert exported_activities.loc[0, "name"] == "Evening Run"
    assert exported_activities.loc[0, "average_heartrate"] == 151.0
    assert exported_activities.loc[0, "max_heartrate"] == 174.0
    assert exported_splits.loc[0, "average_heartrate"] == 149.0
    assert exported_activities.loc[0, "activity_date"] == date(2026, 7, 18)
    assert exported_splits.loc[0, "activity_date"] == date(2026, 7, 18)
    assert not FORBIDDEN_DASHBOARD_COLUMNS.intersection(exported_activities.columns)
    assert not FORBIDDEN_DASHBOARD_COLUMNS.intersection(exported_splits.columns)
    assert metadata["privacy"]["precise_start_times"] == "removed"


def test_activity_date_is_written_as_arrow_date(tmp_path):
    """Parquet stores a calendar date rather than a timestamp."""
    activities = pd.DataFrame(
        {
            "activity_id": [101],
            "start_date_local": ["2026-07-18T18:34:21"],
        }
    )
    splits = pd.DataFrame(
        {
            "activity_id": [101],
            "start_date_local": ["2026-07-18T18:34:21"],
        }
    )

    activities_path, splits_path, _ = export_dashboard_parquet(activities, splits, tmp_path)

    assert str(parquet.read_schema(activities_path).field("activity_date").type) == "date32[day]"
    assert str(parquet.read_schema(splits_path).field("activity_date").type) == "date32[day]"


def test_export_contains_runs_only(tmp_path):
    """Non-running activities and their splits are excluded from dashboard Parquet."""
    activities = pd.DataFrame(
        {
            "activity_id": [101, 202],
            "name": ["Morning Run", "Afternoon Ride"],
            "activity_type": ["Run", "Ride"],
            "start_date_local": [
                "2026-07-18T08:00:00",
                "2026-07-18T14:00:00",
            ],
        }
    )
    splits = pd.DataFrame(
        {
            "activity_id": [101, 202],
            "split_index": [1, 1],
            "start_date_local": [
                "2026-07-18T08:00:00",
                "2026-07-18T14:00:00",
            ],
        }
    )

    activities_path, splits_path, metadata_path = export_dashboard_parquet(
        activities, splits, tmp_path
    )

    exported_activities = pd.read_parquet(activities_path)
    exported_splits = pd.read_parquet(splits_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert exported_activities["activity_id"].tolist() == [101]
    assert exported_splits["activity_id"].tolist() == [101]
    assert metadata["scope"]["activity_types"] == ["Run"]
