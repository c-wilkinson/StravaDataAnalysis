"""Tests for shared static and interactive chart calculations."""

import pandas as pd

from strava_data.strava_api.processing.analytics import (
    activity_heart_rate_summary,
    filter_run_data,
    cumulative_distance,
    monthly_distance,
    monthly_pace,
    prepare_activities,
    rolling_distance,
    run_rest_summary,
)


def _activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "activity_id": [1, 2, 3],
            "name": ["Five", "Ten", "Recovery"],
            "activity_type": ["Run", "Run", "Run"],
            "distance_m": [5000.0, 10000.0, 4000.0],
            "moving_time_s": [1500, 3300, 1320],
            "total_elevation_gain_m": [20.0, 80.0, 10.0],
            "activity_date": ["2026-06-30", "2026-07-01", "2026-07-03"],
        }
    )


def _splits() -> pd.DataFrame:
    rows = []
    for activity_id, activity_date, paces in (
        (1, "2026-06-30", [300, 305, 310]),
        (2, "2026-07-01", [290, 295, 300]),
    ):
        for split_index, pace in enumerate(paces, start=1):
            rows.append(
                {
                    "activity_id": activity_id,
                    "activity_date": activity_date,
                    "distance_m": 1000.0,
                    "elapsed_time_s": pace,
                    "moving_time_s": pace,
                    "split_index": split_index,
                    "elevation_difference_m": 0.0,
                    "average_heartrate": 150.0,
                }
            )
    return pd.DataFrame(rows)


def test_shared_distance_aggregations():
    """Distance functions expose reusable DataFrames for both renderers."""
    prepared = prepare_activities(_activities())
    monthly = monthly_distance(_activities())
    cumulative = cumulative_distance(_activities())
    rolling = rolling_distance(_activities(), window_days=2)

    assert prepared["distance_km"].tolist() == [5.0, 10.0, 4.0]
    assert monthly["distance_km"].tolist() == [5.0, 14.0]
    assert cumulative["cumulative_distance_km"].tolist() == [5.0, 15.0, 19.0]
    assert rolling.iloc[-1]["rolling_distance_km"] == 4.0


def test_shared_pace_and_run_rest_aggregations():
    """Pace and consistency calculations work on date-only split data."""
    pace = monthly_pace(_splits())
    run_rest = run_rest_summary(_activities())

    assert pace["fastest_pace_sec_km"].tolist() == [300.0, 290.0]
    assert pace["median_pace_sec_km"].tolist() == [305.0, 295.0]
    july = run_rest[(run_rest["year"] == 2026) & (run_rest["month"] == 7)].iloc[0]
    assert july["run_days"] == 2
    assert july["rest_days"] == 1


def test_filter_run_data_removes_other_activity_types_and_their_splits():
    """Dashboard processing keeps runs and their corresponding splits only."""
    activities = pd.DataFrame(
        {
            "activity_id": [1, 2, 3],
            "activity_type": ["Run", "Ride", "Walk"],
        }
    )
    splits = pd.DataFrame(
        {
            "activity_id": [1, 1, 2, 3],
            "split_index": [1, 2, 1, 1],
        }
    )

    run_activities, run_splits = filter_run_data(activities, splits)

    assert run_activities["activity_id"].tolist() == [1]
    assert run_splits["activity_id"].tolist() == [1, 1]


def test_activity_heart_rate_summary_fills_historical_nulls_from_splits():
    """Older activity rows use a weighted split average and highest split value."""
    activities = pd.DataFrame(
        {
            "activity_id": [1],
            "activity_date": ["2026-07-01"],
            "average_heartrate": [None],
            "max_heartrate": [None],
        }
    )
    splits = pd.DataFrame(
        {
            "activity_id": [1, 1],
            "activity_date": ["2026-07-01", "2026-07-01"],
            "distance_m": [1000.0, 1000.0],
            "elapsed_time_s": [300.0, 600.0],
            "moving_time_s": [300.0, 600.0],
            "average_heartrate": [130.0, 150.0],
            "split_index": [1, 2],
        }
    )

    summary = activity_heart_rate_summary(activities, splits).iloc[0]

    assert round(summary["average_heartrate"], 2) == 143.33
    assert summary["max_heartrate"] == 150.0
    assert bool(summary["average_heartrate_from_splits"])
    assert bool(summary["max_heartrate_from_splits"])


def test_activity_heart_rate_summary_preserves_activity_level_values():
    """Values obtained directly from the activity remain authoritative."""
    activities = pd.DataFrame(
        {
            "activity_id": [1],
            "activity_date": ["2026-07-01"],
            "average_heartrate": [142.0],
            "max_heartrate": [171.0],
        }
    )
    splits = pd.DataFrame(
        {
            "activity_id": [1],
            "activity_date": ["2026-07-01"],
            "distance_m": [1000.0],
            "elapsed_time_s": [300.0],
            "moving_time_s": [300.0],
            "average_heartrate": [150.0],
            "split_index": [1],
        }
    )

    summary = activity_heart_rate_summary(activities, splits).iloc[0]

    assert summary["average_heartrate"] == 142.0
    assert summary["max_heartrate"] == 171.0
    assert not bool(summary["average_heartrate_from_splits"])
    assert not bool(summary["max_heartrate_from_splits"])
