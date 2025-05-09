"""
Generates a weekly training recommendation chart based on recent Strava activity.

- Analyses the past 6 months to determine usual running days.
- Reviews the last 8 weeks of runs to identify missing session types.
- Uses historical pace data to tailor pace suggestions.
- Assigns recommended runs to the days you typically train.
- Outputs a visual table chart: Suggested_Training_Week.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table
from collections import Counter
from datetime import datetime, timedelta

from strava_data.strava_api.visualisation.utils import (
    prepare_dated_activities,
    format_pace,
    save_and_close_plot,
)
from strava_data.ml.run_type_classifier import cluster_run_types, build_run_features
from strava_data.ml.utils import prepare_pace_summary
from utils.logger import get_logger

LOGGER = get_logger()


def generate_training_plan_chart(
    activities_df: pd.DataFrame, splits_df: pd.DataFrame, output_path: str
) -> None:
    """
    Creates a weekly training schedule PNG file based on training frequency and gaps.

    Parameters:
        activities_df (pd.DataFrame): DataFrame of all Strava activities.
        splits_df (pd.DataFrame): DataFrame of split-level data for pace analysis.
        output_path (str): Path where the training plan chart should be saved.
    """
    LOGGER.info("Generating training recommendation chart...")

    six_months_ago = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=6)
    recent_data = prepare_dated_activities(activities_df)
    recent_data = recent_data[recent_data["start_date"] >= six_months_ago]
    recent_data["day"] = recent_data["start_date"].dt.day_name()
    day_freq = Counter(recent_data["day"])
    preferred_days = [d for d, _ in day_freq.most_common()]
    eight_weeks_ago = pd.Timestamp.now(tz="UTC") - pd.DateOffset(weeks=8)
    recent_splits = splits_df.copy()
    recent_splits["start_date"] = pd.to_datetime(recent_splits["start_date_local"])
    recent_splits = recent_splits[recent_splits["start_date"] >= eight_weeks_ago]
    run_features = build_run_features(splits_df)
    clustered = cluster_run_types(run_features)
    recent_runs = clustered[clustered["start_date"] >= eight_weeks_ago]
    run_counts = Counter(recent_runs["run_type"])
    pace_data = prepare_pace_summary(recent_splits, group_cols=["activity_id"])
    median_pace = pace_data["pace_median"].median()
    fast_pace = pace_data["pace_median"].quantile(0.25)
    slow_pace = pace_data["pace_median"].quantile(0.75)

    def suggest_bounds(pace: float, tolerance: float = 0.05) -> str:
        low = pace * (1 - tolerance)
        high = pace * (1 + tolerance)
        return f"{format_pace(low, None)} – {format_pace(high, None)}"

    ideal_mix = ["Long", "Tempo", "Intervals", "Recovery"]
    weekly_counts = recent_data.groupby(recent_data["start_date"].dt.isocalendar().week).size()
    average_weekly_runs = int(round(weekly_counts.mean() + 0.5))
    max_recommendations = max(3, min(5, average_weekly_runs))
    recommendations = []
    run_scores = {
        "Long": 1.0 - (run_counts.get("Long", 0) / 4),
        "Tempo": 1.0 - (run_counts.get("Tempo", 0) / 4),
        "Intervals": 1.0 - (run_counts.get("Intervals", 0) / 3),
        "Recovery": 1.0 - (run_counts.get("Recovery", 0) / 2),
    }

    sorted_types = sorted(run_scores.items(), key=lambda x: x[1], reverse=True)

    for run_type, _ in sorted_types:
        if len(recommendations) >= max_recommendations:
            break
        if run_type == "Intervals":
            recommendations.append(
                {
                    "type": "Intervals",
                    "intensity": "Hard",
                    "distance": "6x400m",
                    "pace": suggest_bounds(fast_pace),
                    "reason": "Include interval session to improve VO2 max.",
                }
            )
        elif run_type == "Long":
            recommendations.append(
                {
                    "type": "Long",
                    "intensity": "Easy",
                    "distance": "14–18 km",
                    "pace": suggest_bounds(slow_pace),
                    "reason": "Endurance run builds aerobic fitness.",
                }
            )
        elif run_type == "Tempo":
            recommendations.append(
                {
                    "type": "Tempo",
                    "intensity": "Moderate–Hard",
                    "distance": "6–10 km",
                    "pace": suggest_bounds(median_pace),
                    "reason": "Tempo runs increase lactate threshold.",
                }
            )
        elif run_type == "Recovery":
            recommendations.append(
                {
                    "type": "Recovery",
                    "intensity": "Easy",
                    "distance": "5 km",
                    "pace": suggest_bounds(slow_pace),
                    "reason": "Recovery run supports adaptation.",
                }
            )

    recommendations = recommendations[:max_recommendations]  # cap number of runs
    full_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assigned = dict()
    used_days = set()
    previous_day = None
    for i, rec in enumerate(recommendations):
        for d in preferred_days:
            if d in used_days:
                continue
            if previous_day is not None:
                current_idx = full_week.index(d)
                previous_idx = full_week.index(previous_day)
                if abs(current_idx - previous_idx) in (0, 1):
                    if rec["type"] not in ("Recovery", "Easy") and assigned[previous_day][
                        "type"
                    ] not in ("Recovery", "Easy"):
                        continue  # avoid hard sessions back-to-back
            assigned[d] = rec
            used_days.add(d)
            previous_day = d
            break

    fig, ax = plt.subplots(figsize=(12, len(full_week) * 0.8))
    ax.axis("off")
    table = Table(ax, bbox=[0, 0, 1, 1])
    col_labels = ["Day", "Run Type", "Distance", "Pace", "Intensity", "Reason"]
    cell_text = []
    for day in full_week:
        if day in assigned:
            rec = assigned[day]
            row = [day, rec["type"], rec["distance"], rec["pace"], rec["intensity"], rec["reason"]]
        else:
            row = [day, "Rest", "–", "–", "–", "Scheduled rest day"]
        cell_text.append(row)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for row_idx, row in enumerate([col_labels] + cell_text):
        for col_idx, val in enumerate(row):
            cell_width = [0.08, 0.12, 0.10, 0.10, 0.12, 0.48][col_idx]
            table.add_cell(
                row_idx,
                col_idx,
                cell_width,
                1 / (len(cell_text) + 1),
                text=val,
                loc="center",
                facecolor="#f0f0f0" if row_idx == 0 else "white",
            )
    ax.add_table(table)
    plt.title("Suggested Training Plan (Next Week)", fontsize=14)
    save_and_close_plot(output_path)
