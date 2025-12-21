"""
Render Strava-style summary cards (weekly / monthly / yearly) as PNG images.

Public entrypoint:
- render_week_month_year_cards(activities_df, splits_df)

This module follows the existing visualisation style:
- accepts DataFrames
- does prep + computation internally
- writes PNGs to disk
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import pandas as pd

from strava_data.db.models import Activity
from strava_data.summaries.stats import (
    PeriodStats,
    compute_period_stats,
    make_month_windows,
    make_week_windows,
    make_year_windows,
)
from utils.logger import get_logger

LOGGER = get_logger()


@dataclass(frozen=True)
class CardMetric:
    """
    A single metric line displayed on the summary card.
    """

    label: str
    value: str
    delta: str
    previous: str


@dataclass(frozen=True)
class SplitLite:
    """
    Minimal split representation for summary stats.

    We only need fields required to compute "fastest km".
    """

    activity_id: int
    distance_m: float
    elapsed_time_s: int
    start_date_local: str


def _activities_from_df(activities_df: pd.DataFrame) -> list[Activity]:
    """
    Convert the activities DataFrame into a list of Activity dataclasses.
    """
    activities: list[Activity] = []
    for row in activities_df.itertuples(index=False):
        activities.append(
            Activity(
                activity_id=int(getattr(row, "activity_id")),
                name=str(getattr(row, "name")),
                activity_type=str(getattr(row, "activity_type")),
                distance_m=float(getattr(row, "distance_m")),
                moving_time_s=int(getattr(row, "moving_time_s")),
                average_speed_m_s=float(getattr(row, "average_speed_m_s")),
                max_speed_m_s=float(getattr(row, "max_speed_m_s")),
                total_elevation_gain_m=float(getattr(row, "total_elevation_gain_m")),
                start_date_local=str(getattr(row, "start_date_local")),
                average_cadence=float(getattr(row, "average_cadence")),
            )
        )
    return activities


def _splits_from_df(splits_df: pd.DataFrame) -> list[SplitLite]:
    """
    Convert the splits DataFrame into a list of SplitLite objects.

    The DB schema does not always contain a unique split_id. For summary cards we
    only require activity_id, distance_m, elapsed_time_s, and start_date_local.
    """
    splits: list[SplitLite] = []
    required = {"activity_id", "distance_m", "elapsed_time_s", "start_date_local"}

    if splits_df.empty or not required.issubset(set(splits_df.columns)):
        return splits

    for row in splits_df.itertuples(index=False):
        splits.append(
            SplitLite(
                activity_id=int(getattr(row, "activity_id")),
                distance_m=float(getattr(row, "distance_m")),
                elapsed_time_s=int(getattr(row, "elapsed_time_s")),
                start_date_local=str(getattr(row, "start_date_local")),
            )
        )
    return splits


def _format_prev(value: str) -> str:
    """
    Format a previous-window value for display.
    """
    return f"Prev: {value}"


def _format_prev_if_present(value: str) -> str:
    """
    Format a previous-window value, but keep an em dash if value is not available.
    """
    if value == "—":
        return "Prev: —"
    return _format_prev(value)


def _pct_change(current: float, previous: float) -> Optional[float]:
    """
    Calculate percentage change from previous to current.
    """
    if previous <= 0:
        return None
    return (current - previous) / previous * 100.0


def _format_pct(value: Optional[float]) -> str:
    """
    Format a percentage change for display.
    """
    if value is None:
        return "—"
    sign = "+" if value >= 0 else "−"
    return f"{sign}{abs(value):.0f}%"


def _format_count_delta(current: int, previous: int) -> str:
    """
    Format a signed delta for integer counts.
    """
    diff = current - previous
    if diff == 0:
        return "±0"
    sign = "+" if diff > 0 else "−"
    return f"{sign}{abs(diff)}"


def _format_km(value: Optional[float]) -> str:
    """
    Format a distance in kilometres for display.
    """
    if value is None:
        return "—"
    return f"{value:.1f} km"


def _format_hours(value: float) -> str:
    """
    Format a duration in hours for display.
    """
    return f"{value:.0f} hrs"


def _format_m(value: float) -> str:
    """
    Format a distance in metres for display.
    """
    return f"{int(round(value)):,} m"


def _format_pace(seconds_per_km: Optional[float]) -> str:
    """
    Format a pace value (seconds per km) as mm:ss.
    """
    if seconds_per_km is None or seconds_per_km <= 0:
        return "—"
    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))
    return f"{minutes}:{seconds:02d} /km"


def _pace_delta(current: Optional[float], previous: Optional[float]) -> str:
    """
    Format the change in pace between periods in seconds.

    Negative values indicate an improvement.
    """
    if current is None or previous is None:
        return "—"
    diff = current - previous
    sign = "−" if diff < 0 else "+"
    return f"{sign}{abs(int(round(diff)))}s"


def _build_metrics(current: PeriodStats, previous: PeriodStats) -> Tuple[CardMetric, ...]:
    """
    Build the list of card metrics with values, deltas, and previous-window figures.
    """
    longest_pct: Optional[float] = None
    if current.distance.longest_km is not None and previous.distance.longest_km is not None:
        longest_pct = _pct_change(current.distance.longest_km, previous.distance.longest_km)

    current_fastest = _format_pace(current.pace.fastest_km_s)
    previous_fastest = _format_pace(previous.pace.fastest_km_s)

    return (
        CardMetric(
            label="Activities",
            value=str(current.activities),
            delta=_format_count_delta(current.activities, previous.activities),
            previous=_format_prev(str(previous.activities)),
        ),
        CardMetric(
            label="Total distance",
            value=_format_km(current.distance.total_km),
            delta=_format_pct(_pct_change(current.distance.total_km, previous.distance.total_km)),
            previous=_format_prev(_format_km(previous.distance.total_km)),
        ),
        CardMetric(
            label="Total time",
            value=_format_hours(current.total_time_hours),
            delta=_format_pct(_pct_change(current.total_time_hours, previous.total_time_hours)),
            previous=_format_prev(_format_hours(previous.total_time_hours)),
        ),
        CardMetric(
            label="Total elevation",
            value=_format_m(current.elevation.total_m),
            delta=_format_pct(_pct_change(current.elevation.total_m, previous.elevation.total_m)),
            previous=_format_prev(_format_m(previous.elevation.total_m)),
        ),
        CardMetric(
            label="Avg distance (km)",
            value=_format_km(current.distance.average_km),
            delta=_format_pct(
                _pct_change(current.distance.average_km, previous.distance.average_km)
            ),
            previous=_format_prev(_format_km(previous.distance.average_km)),
        ),
        CardMetric(
            label="Furthest activity",
            value=_format_km(current.distance.longest_km),
            delta=_format_pct(longest_pct),
            previous=_format_prev_if_present(_format_km(previous.distance.longest_km)),
        ),
        CardMetric(
            label="Fastest km",
            value=current_fastest,
            delta=_pace_delta(current.pace.fastest_km_s, previous.pace.fastest_km_s),
            previous=_format_prev_if_present(previous_fastest),
        ),
    )


def _create_card_figure(width_px: int, height_px: int, dpi: int) -> Figure:
    """
    Create and configure the matplotlib figure for a summary card.
    """
    fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor("#0b0b0f")
    return fig


def _draw_header(axis: Axes, current: PeriodStats) -> None:
    """
    Draw the title and date range at the top of the summary card.
    """
    axis.text(
        0.08,
        0.93,
        current.window.label,
        fontsize=42,
        fontweight="bold",
        color="white",
        ha="left",
        va="center",
    )

    date_range = f"{current.window.start:%d %b %Y} – {current.window.end:%d %b %Y}"
    axis.text(
        0.08,
        0.875,
        date_range,
        fontsize=20,
        color="#c9c9d1",
        ha="left",
        va="center",
    )


def _draw_metrics_grid(axis: Axes, metrics: Sequence[CardMetric]) -> None:
    """
    Draw the metrics grid section of the summary card.
    """
    for index, metric in enumerate(metrics):
        is_left = index % 2 == 0
        column_x = 0.08 if is_left else 0.55
        meta_x = 0.47 if is_left else 0.97

        row_y = 0.74 - (index // 2) * 0.18

        label_y = row_y
        value_y = row_y - 0.055
        prev_y = row_y - 0.105

        axis.text(
            column_x,
            label_y,
            metric.label,
            fontsize=16,
            color="#c9c9d1",
            ha="left",
            va="center",
        )
        axis.text(
            column_x,
            value_y,
            metric.value,
            fontsize=30,
            color="white",
            ha="left",
            va="center",
        )
        axis.text(
            meta_x,
            value_y,
            metric.delta,
            fontsize=16,
            color="#c9c9d1",
            ha="right",  # key: keep inside edge
            va="center",
        )
        axis.text(
            meta_x,
            prev_y,
            metric.previous,
            fontsize=12,
            color="#9ea0aa",
            ha="right",  # key: keep inside edge
            va="center",
        )


def _draw_footer(axis: Axes) -> None:
    """
    Draw the footer text on the summary card.
    """
    axis.text(
        0.08,
        0.06,
        "Generated from data gathered with Garmin and stored in Strava",
        fontsize=8,
        color="#c9c9d1",
        ha="left",
        va="center",
    )


def _render_summary_card(current: PeriodStats, previous: PeriodStats, output_path: Path) -> None:
    """
    Render a single summary card image to disk.
    """
    fig = _create_card_figure(width_px=1800, height_px=1000, dpi=150)
    axis = fig.add_axes([0, 0, 1, 1])
    axis.set_axis_off()

    _draw_header(axis, current)
    _draw_metrics_grid(axis, _build_metrics(current, previous))
    _draw_footer(axis)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _compute_week_month_year_stats(
    activities: Sequence[Activity],
    splits: Sequence[SplitLite],
    as_of: datetime,
) -> Tuple[
    Tuple[PeriodStats, PeriodStats],
    Tuple[PeriodStats, PeriodStats],
    Tuple[PeriodStats, PeriodStats],
]:
    """
    Compute current and previous stats for week, month, and year windows.
    """
    week_window, prev_week_window = make_week_windows(as_of)
    month_window, prev_month_window = make_month_windows(as_of)
    year_window, prev_year_window = make_year_windows(as_of)

    weekly = (
        compute_period_stats(week_window, activities, splits),
        compute_period_stats(prev_week_window, activities, splits),
    )
    monthly = (
        compute_period_stats(month_window, activities, splits),
        compute_period_stats(prev_month_window, activities, splits),
    )
    yearly = (
        compute_period_stats(year_window, activities, splits),
        compute_period_stats(prev_year_window, activities, splits),
    )
    LOGGER.info(
        "Weekly window: %s -> %s | activities=%d",
        week_window.start.date(),
        week_window.end.date(),
        weekly[0].activities,
    )
    LOGGER.info(
        "Monthly window: %s -> %s | activities=%d",
        month_window.start.date(),
        month_window.end.date(),
        monthly[0].activities,
    )
    LOGGER.info(
        "Yearly window: %s -> %s | activities=%d",
        year_window.start.date(),
        year_window.end.date(),
        yearly[0].activities,
    )
    return weekly, monthly, yearly


def _render_all_cards(
    weekly: Tuple[PeriodStats, PeriodStats],
    monthly: Tuple[PeriodStats, PeriodStats],
    yearly: Tuple[PeriodStats, PeriodStats],
) -> None:
    """
    Render all summary cards using fixed output filenames.
    """
    week_stats, prev_week_stats = weekly
    month_stats, prev_month_stats = monthly
    year_stats, prev_year_stats = yearly

    _render_summary_card(week_stats, prev_week_stats, Path("1_summary_card_weekly.png"))
    _render_summary_card(month_stats, prev_month_stats, Path("2_summary_card_monthly.png"))
    _render_summary_card(year_stats, prev_year_stats, Path("3_summary_card_yearly.png"))


def render_week_month_year_cards(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """
    Generate weekly, monthly, and yearly summary card images from activity data.

    Output files:
    - 1_summary_card_weekly.png
    - 2_summary_card_monthly.png
    - 3_summary_card_yearly.png
    """
    if activities_df.empty:
        return

    activities = _activities_from_df(activities_df)
    splits = _splits_from_df(splits_df) if not splits_df.empty else []
    as_of = datetime.now()
    LOGGER.info("Summary cards anchor date (as_of): %s", as_of.isoformat())
    LOGGER.info(
        "Activities date range in DB: %s -> %s",
        activities_df["start_date_local"].min(),
        activities_df["start_date_local"].max(),
    )
    if "start_date_local" in activities_df.columns and not activities_df["start_date_local"].empty:
        latest = pd.to_datetime(
            activities_df["start_date_local"],
            errors="coerce",
            utc=True,
        ).dropna()

        if not latest.empty:
            latest_dt = latest.max().to_pydatetime()
            as_of = datetime(
                latest_dt.year,
                latest_dt.month,
                latest_dt.day,
                23,
                59,
                59,
            )

    LOGGER.info("Converted %d activities", len(activities))
    LOGGER.info("Converted %d splits (lite)", len(splits))
    weekly, monthly, yearly = _compute_week_month_year_stats(activities, splits, as_of)
    _render_all_cards(weekly, monthly, yearly)
