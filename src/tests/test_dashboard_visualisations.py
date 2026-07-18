"""Smoke tests for the interactive Plotly figure builders."""

import pandas as pd
import plotly.graph_objects as go

from strava_data.strava_api.visualisation import (
    graphs_distance,
    graphs_distribution,
    graphs_effort,
    graphs_ml,
    graphs_pace,
)


def _activities() -> pd.DataFrame:
    rows = []
    for index in range(1, 9):
        rows.append(
            {
                "activity_id": index,
                "name": f"Run {index}",
                "activity_type": "Run",
                "distance_m": 5000.0 + (index * 500),
                "moving_time_s": 1500 + (index * 30),
                "average_speed_m_s": 3.3,
                "max_speed_m_s": 4.2,
                "total_elevation_gain_m": 20.0 + index,
                "activity_date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=index * 14),
                "average_cadence": 170.0 + index,
                "average_heartrate": 145.0 + index,
                "max_heartrate": 170.0 + index,
                "is_outdoor": 1,
            }
        )
    return pd.DataFrame(rows)


def _splits() -> pd.DataFrame:
    rows = []
    for activity_id in range(1, 9):
        activity_date = pd.Timestamp("2026-01-01") + pd.Timedelta(days=activity_id * 14)
        for split_index in range(1, 6):
            pace = 330 - (activity_id * 2) + split_index
            rows.append(
                {
                    "split_row_id": len(rows) + 1,
                    "activity_id": activity_id,
                    "distance_m": 1000.0,
                    "elapsed_time_s": pace,
                    "elevation_difference_m": float(split_index - 3),
                    "moving_time_s": pace,
                    "pace_zone": 2,
                    "split_index": split_index,
                    "average_grade_adjusted_speed_m_s": 3.2,
                    "average_heartrate": 145.0 + activity_id,
                    "activity_date": activity_date,
                }
            )
    return pd.DataFrame(rows)


def test_non_empty_plotly_builders_return_figures():
    """Every dashboard chart family can render exported Parquet-shaped data."""
    activities = _activities()
    splits = _splits()
    figures = [
        graphs_distance.build_monthly_distance_figure(activities),
        graphs_distance.build_cumulative_distance_figure(activities),
        graphs_distance.build_rolling_distance_figure(activities),
        graphs_distance.build_pace_vs_total_distance_figure(splits),
        graphs_pace.build_running_pace_figure(splits),
        graphs_pace.build_fastest_1km_pace_figure(splits),
        graphs_effort.build_training_load_figure(activities),
        graphs_effort.build_vo2_proxy_figure(splits),
        graphs_distribution.build_activity_heatmap_figure(activities),
        graphs_distribution.build_heart_rate_zone_figure(splits),
        graphs_ml.build_run_cluster_figure(splits),
        graphs_ml.build_pace_forecast_figure(splits),
    ]

    assert all(isinstance(figure, go.Figure) for figure in figures)
    assert all(figure.data for figure in figures)


def test_empty_plotly_builders_are_safe():
    """Dashboard pages can render useful empty states without chart errors."""
    empty = pd.DataFrame()
    figures = [
        graphs_distance.build_monthly_distance_figure(empty),
        graphs_pace.build_running_pace_figure(empty),
        graphs_effort.build_training_load_figure(empty),
        graphs_distribution.build_activity_heatmap_figure(empty),
        graphs_ml.build_pace_forecast_figure(empty),
    ]

    assert all(isinstance(figure, go.Figure) for figure in figures)
    assert all(not figure.data for figure in figures)


def test_calendar_categories_use_expected_order():
    """Calendar-based charts use conventional month and weekday ordering."""
    activities = pd.concat(
        [
            _activities(),
            pd.DataFrame(
                [
                    {
                        "activity_id": 99,
                        "name": "Previous year",
                        "activity_type": "Run",
                        "distance_m": 5000.0,
                        "moving_time_s": 1500,
                        "total_elevation_gain_m": 20.0,
                        "activity_date": pd.Timestamp("2025-11-15"),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    monthly_figure = graphs_distance.build_monthly_distance_by_year_figure(activities)
    weekday_figure = graphs_pace.build_pace_by_day_figure(_splits())

    assert list(monthly_figure.layout.xaxis.categoryarray) == [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    assert list(weekday_figure.layout.xaxis.categoryarray) == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]


def test_activity_calendar_has_one_readable_row_per_year():
    """The activity calendar renders each calendar year as a separate heatmap."""
    activities = pd.concat(
        [
            _activities(),
            pd.DataFrame(
                [
                    {
                        "activity_id": 99,
                        "name": "Previous year",
                        "activity_type": "Run",
                        "distance_m": 5000.0,
                        "moving_time_s": 1500,
                        "total_elevation_gain_m": 20.0,
                        "activity_date": pd.Timestamp("2025-11-15"),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    figure = graphs_distribution.build_activity_heatmap_figure(activities)

    assert len(figure.data) == 2
    assert all(trace.type == "heatmap" for trace in figure.data)
    assert list(figure.data[0].y) == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    assert figure.layout.height >= 360
