"""
Generates a weekly training recommendation chart based on recent Strava activity.

- Analyses the past 6 months to determine usual running days.
- Reviews the last 8 weeks of runs to identify missing session types.
- Uses historical pace data to tailor pace suggestions.
- Assigns recommended runs to the days you typically train.
- Outputs a visual table chart: Suggested_Training_Week.png
"""

from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table

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
    Generates and saves a visual weekly training plan as a PNG file.

    This function analyses recent training behaviour and fitness gaps to suggest
    up to 5 structured runs per week. The resulting schedule balances intensity,
    avoids overtraining, and aligns with the user's typical running days.

    Parameters:
        activities_df (pd.DataFrame): DataFrame of all Strava activity-level data.
        splits_df (pd.DataFrame): DataFrame of all split-level running data.
        output_path (str): File path where the training plan image will be saved.
    """
    LOGGER.info("Generating training recommendation chart...")

    (
        preferred_days,
        run_counts,
        fast_pace,
        median_pace,
        slow_pace,
        max_recommendations,
    ) = _get_recent_data(activities_df, splits_df)

    recommendations = _generate_recommendations(
        run_counts, fast_pace, median_pace, slow_pace, max_recommendations
    )

    assigned = _assign_runs_to_days(recommendations, preferred_days)
    _render_training_table(assigned, output_path)


def _get_recent_data(activities_df, splits_df):
    """
    Extracts recent training metadata needed to generate a personalised training plan.

    This includes:
    - The user's preferred training days (based on frequency over 6 months)
    - Run type distribution over the past 8 weeks
    - Recent representative pace metrics (fast, median, slow)
    - Target number of runs to recommend this week

    Parameters:
        activities_df (pd.DataFrame): DataFrame of all Strava activities.
        splits_df (pd.DataFrame): DataFrame of all split-level records.

    Returns:
        tuple:
            preferred_days (list): Ordered list of most common training days.
            run_counts (Counter): Frequency of run types over recent period.
            fast_pace (float): 25th percentile pace in seconds/km.
            median_pace (float): Median pace in seconds/km.
            slow_pace (float): 75th percentile pace in seconds/km.
            max_recommendations (int): Number of runs to recommend this week.
    """
    preferred_days, recent_data = _get_recent_days(activities_df)
    recent_splits = _get_recent_splits(splits_df)
    run_counts = _get_recent_run_counts(splits_df, recent_splits)
    pace_data = prepare_pace_summary(recent_splits, group_cols=["activity_id"])
    median_pace = pace_data["pace_median"].median()
    fast_pace = pace_data["pace_median"].quantile(0.25)
    slow_pace = pace_data["pace_median"].quantile(0.75)

    weekly_counts = recent_data.groupby(recent_data["start_date"].dt.isocalendar().week).size()
    average_weekly_runs = int(round(weekly_counts.mean() + 0.5))
    max_recommendations = max(3, min(5, average_weekly_runs))

    return preferred_days, run_counts, fast_pace, median_pace, slow_pace, max_recommendations


def _get_recent_run_counts(splits_df: pd.DataFrame, recent_splits: pd.DataFrame) -> Counter:
    """
    Computes the frequency of run types over the recent training period.

    Uses clustering to classify runs into types (e.g. Long, Tempo, Recovery, Intervals),
    then filters to include only runs from the same window as recent_splits.

    Parameters:
        splits_df (pd.DataFrame): Full split-level dataset for building run features.
        recent_splits (pd.DataFrame): Date-filtered splits used to define the recent period.

    Returns:
        Counter: A mapping of run type labels to their counts over the recent period.
    """
    run_features = build_run_features(splits_df)
    clustered = cluster_run_types(run_features)
    recent_runs = clustered[clustered["start_date"] >= recent_splits["start_date"].min()]
    return Counter(recent_runs["run_type"])


def _get_recent_days(activities_df):
    """
    Identifies the user's most common training days over the past 6 months.

    Filters activities to the last 6 months and counts frequency of runs per day of the week.

    Parameters:
        activities_df (pd.DataFrame): DataFrame containing all activity records.

    Returns:
        tuple:
            preferred_days (list): Day names ordered by frequency of runs.
            recent_data (pd.DataFrame): Filtered DataFrame with activities from the past 6 months.
    """
    six_months_ago = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=6)
    recent_data = prepare_dated_activities(activities_df)
    recent_data = recent_data[recent_data["start_date"] >= six_months_ago]
    recent_data["day"] = recent_data["start_date"].dt.day_name()
    day_freq = Counter(recent_data["day"])
    preferred_days = [d for d, _ in day_freq.most_common()]
    return preferred_days, recent_data


def _get_recent_splits(splits_df):
    """
    Filters split-level data to include only entries from the past 8 weeks.

    Converts 'start_date_local' to UTC-naive datetime and filters by date threshold.

    Parameters:
        splits_df (pd.DataFrame): DataFrame containing all split records.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only recent splits.
    """
    eight_weeks_ago = pd.Timestamp.now(tz="UTC") - pd.DateOffset(weeks=8)
    recent_splits = splits_df.copy()
    recent_splits["start_date"] = pd.to_datetime(recent_splits["start_date_local"])
    return recent_splits[recent_splits["start_date"] >= eight_weeks_ago]


def _suggest_bounds(pace: float, tolerance: float = 0.05) -> str:
    """
    Returns a formatted pace range string based on a central pace value and tolerance.

    Parameters:
        pace (float): Central pace in seconds per kilometre.
        tolerance (float): Proportional margin around the pace (default is 5%).

    Returns:
        str: Formatted pace range string (e.g. "4:45 – 5:00").
    """
    low = pace * (1 - tolerance)
    high = pace * (1 + tolerance)
    return f"{format_pace(low, None)} – {format_pace(high, None)}"


def _generate_recommendations(run_counts, fast_pace, median_pace, slow_pace, max_recommendations):
    """
    Generates a list of recommended training sessions to improve fitness balance.

    Scores run types based on recent frequency and prioritises under-represented types.
    Uses recent pace data to personalise pace ranges for each session type.
    Limits output to a maximum number of recommendations.

    Parameters:
        run_counts (Counter): Frequency of each run type over the recent period.
        fast_pace (float): 25th percentile pace from recent runs (used for intervals).
        median_pace (float): Median pace from recent runs (used for tempo).
        slow_pace (float): 75th percentile pace from recent runs (used for long and recovery).
        max_recommendations (int): Maximum number of runs to recommend in the week.

    Returns:
        list: Recommended run dicts including type, distance, intensity, pace, and rationale.
    """

    run_scores = {
        "Long": 1.0 - (run_counts.get("Long", 0) / 4),
        "Tempo": 1.0 - (run_counts.get("Tempo", 0) / 4),
        "Intervals": 1.0 - (run_counts.get("Intervals", 0) / 3),
        "Recovery": 1.0 - (run_counts.get("Recovery", 0) / 2),
    }
    sorted_types = sorted(run_scores.items(), key=lambda x: x[1], reverse=True)
    recommendations = []

    for run_type, _ in sorted_types:
        if len(recommendations) >= max_recommendations:
            break
        if run_type == "Intervals":
            recommendations.append(
                {
                    "type": "Intervals",
                    "intensity": "Hard",
                    "distance": "6x400m",
                    "pace": _suggest_bounds(fast_pace),
                    "reason": "Include interval session to improve VO2 max.",
                }
            )
        elif run_type == "Long":
            recommendations.append(
                {
                    "type": "Long",
                    "intensity": "Easy",
                    "distance": "14–18 km",
                    "pace": _suggest_bounds(slow_pace),
                    "reason": "Endurance run builds aerobic fitness.",
                }
            )
        elif run_type == "Tempo":
            recommendations.append(
                {
                    "type": "Tempo",
                    "intensity": "Moderate–Hard",
                    "distance": "6–10 km",
                    "pace": _suggest_bounds(median_pace),
                    "reason": "Tempo runs increase lactate threshold.",
                }
            )
        elif run_type == "Recovery":
            recommendations.append(
                {
                    "type": "Recovery",
                    "intensity": "Easy",
                    "distance": "5 km",
                    "pace": _suggest_bounds(slow_pace),
                    "reason": "Recovery run supports adaptation.",
                }
            )

    return recommendations


def _assign_runs_to_days(recommendations, preferred_days):
    """
    Assigns recommended training sessions to days of the week based on historical patterns.

    Prioritises days the user typically trains (based on recent activity),
    avoids back-to-back hard sessions, and fills up to the number of recommended runs.

    Parameters:
        recommendations (list): A list of run recommendation dicts, each containing type, pace, etc.
        preferred_days (list): Days of the week sorted by user's historical training frequency.

    Returns:
        dict: A mapping of day name to assigned run recommendation.
    """
    full_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assigned = {}
    used_days = set()
    previous_day = None

    for rec in recommendations:
        for day_candidate in preferred_days:
            if day_candidate in used_days:
                continue
            if previous_day is not None:
                current_idx = full_week.index(day_candidate)
                previous_idx = full_week.index(previous_day)
                if abs(current_idx - previous_idx) in (0, 1):
                    if rec["type"] not in ("Recovery", "Easy") and assigned[previous_day][
                        "type"
                    ] not in ("Recovery", "Easy"):
                        continue
            assigned[day_candidate] = rec
            used_days.add(day_candidate)
            previous_day = day_candidate
            break

    return assigned


def _render_training_table(assigned, output_path):
    """
    Renders a visual training plan as a PNG table.

    Creates a 7-row table showing daily training recommendations using matplotlib.
    Each row includes the day, run type, distance, pace range, intensity, and reason.
    Rest days are automatically filled for unassigned days.

    Parameters:
        assigned (dict): Mapping of day name (e.g. "Monday") to a run recommendation dict.
        output_path (str): File path where the output PNG image should be saved.
    """
    full_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    _, plot_axis = plt.subplots(figsize=(12, len(full_week) * 0.8))
    plot_axis.axis("off")
    table = Table(plot_axis, bbox=[0, 0, 1, 1])
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

    plot_axis.add_table(table)
    plt.title("Suggested Training Plan (Next Week)", fontsize=14)
    save_and_close_plot(output_path)
