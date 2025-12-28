"""
Compute deterministic week/month/year summary stats from Activity and Split models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence, Tuple

from dateutil import parser

from strava_data.db.models import Activity, Split


@dataclass(frozen=True)
class Window:
    """
    A labelled time window.
    """

    label: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class DistanceStats:
    """
    Distance-related stats.
    """

    total_km: float
    average_km: float
    longest_km: Optional[float]


@dataclass(frozen=True)
class ElevationStats:
    """
    Elevation-related stats.
    """

    total_m: float
    average_m: float


@dataclass(frozen=True)
class PaceStats:
    """
    Pace-related stats.
    """

    fastest_km_s: Optional[float]


@dataclass(frozen=True)
class PeriodStats:
    """
    Summary stats for a time window.
    """

    window: Window
    activities: int
    total_time_hours: float
    distance: DistanceStats
    elevation: ElevationStats
    pace: PaceStats


def _parse_start_date_local(start_date_local: str) -> datetime:
    """
    Parse Activity/Split.start_date_local into a naive UTC datetime.
    """
    parsed = parser.parse(start_date_local)

    if parsed.tzinfo is None:
        return parsed

    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _in_range(activity_date: datetime, start: datetime, end: datetime) -> bool:
    """
    Return True if activity_date is within [start, end].
    """
    return start <= activity_date <= end


def _km(meters: float) -> float:
    """
    Convert metres to kilometres.
    """
    return meters / 1000.0


def _hours(seconds: int) -> float:
    """
    Convert seconds to hours.
    """
    return seconds / 3600.0


def _fastest_km_seconds(splits: Sequence[Split]) -> Optional[float]:
    """
    Return the fastest ~1 km split time in seconds.
    If no ~1km split exists, we fall back to the fastest split available.
    """
    if not splits:
        return None

    candidates = [split for split in splits if 950.0 <= split.distance_m <= 1050.0]
    pool = candidates if candidates else list(splits)
    return float(min(split.elapsed_time_s for split in pool))


def compute_period_stats(
    window: Window, activities: Sequence[Activity], splits: Sequence[Split]
) -> PeriodStats:
    """
    Compute summary stats for the given window.

    Parameters
    ----------
    window:
        The time window (label, start, end).
    activities:
        All activities (we will filter to those within the window).
    splits:
        All splits (we will filter to those belonging to activities in the window).

    Returns
    -------
    PeriodStats
        Structured stats suitable for rendering cards/graphs.
    """
    activities_in_window = [
        activity
        for activity in activities
        if _in_range(
            _parse_start_date_local(activity.start_date_local),
            window.start,
            window.end,
        )
    ]
    activity_ids = {activity.activity_id for activity in activities_in_window}

    splits_in_window = [
        split
        for split in splits
        if split.activity_id in activity_ids
        and _in_range(
            _parse_start_date_local(split.start_date_local),
            window.start,
            window.end,
        )
    ]

    activity_count = len(activities_in_window)

    total_distance_km = _km(sum(activity.distance_m for activity in activities_in_window))
    total_time_hours = _hours(sum(activity.moving_time_s for activity in activities_in_window))
    total_elevation_m = float(
        sum(activity.total_elevation_gain_m for activity in activities_in_window)
    )

    longest_km: Optional[float] = None
    if activities_in_window:
        longest_km = _km(max(activity.distance_m for activity in activities_in_window))

    average_km = total_distance_km / activity_count if activity_count > 0 else 0.0
    average_elevation_m = total_elevation_m / activity_count if activity_count > 0 else 0.0

    fastest_km_s = _fastest_km_seconds(splits_in_window)

    return PeriodStats(
        window=window,
        activities=activity_count,
        total_time_hours=total_time_hours,
        distance=DistanceStats(
            total_km=total_distance_km,
            average_km=average_km,
            longest_km=longest_km,
        ),
        elevation=ElevationStats(
            total_m=total_elevation_m,
            average_m=average_elevation_m,
        ),
        pace=PaceStats(
            fastest_km_s=fastest_km_s,
        ),
    )


def make_week_windows(as_of: datetime) -> Tuple[Window, Window]:
    """
    Build full calendar week windows.

    Week starts on Monday and ends on Sunday, regardless of activity presence.
    - Current: Monday 00:00:00 -> Sunday 23:59:59 (week containing as_of)
    - Previous: Monday 00:00:00 -> Sunday 23:59:59 (week before current)
    """
    week_start = (as_of - timedelta(days=as_of.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)

    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(seconds=1)

    return (
        Window(label="Week", start=week_start, end=week_end),
        Window(label="Week", start=prev_start, end=prev_end),
    )


def make_month_windows(as_of: datetime) -> Tuple[Window, Window]:
    """
    Build full calendar month windows.

    Month starts on the 1st and ends on the last day, regardless of activity presence.
    - Current: 1st 00:00:00 -> last day 23:59:59 (month containing as_of)
    - Previous: 1st 00:00:00 -> last day 23:59:59 (month before current)
    """
    month_start = as_of.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # First moment of next month
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    month_end = next_month_start - timedelta(seconds=1)

    # Previous month start
    if month_start.month == 1:
        prev_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_start = month_start.replace(month=month_start.month - 1)

    prev_end = month_start - timedelta(seconds=1)

    return (
        Window(label="Month", start=month_start, end=month_end),
        Window(label="Month", start=prev_start, end=prev_end),
    )


def make_year_windows(as_of: datetime) -> Tuple[Window, Window]:
    """
    Build calendar year-to-date vs previous calendar year windows.

    - Current: Jan 1 of current year -> as_of
    - Previous: Jan 1 -> Dec 31 of previous year
    """
    year_start = datetime(as_of.year, 1, 1, 0, 0, 0)
    next_year_start = datetime(as_of.year + 1, 1, 1, 0, 0, 0)
    year_end = next_year_start - timedelta(seconds=1)

    prev_start = datetime(as_of.year - 1, 1, 1, 0, 0, 0)
    prev_end = year_start - timedelta(seconds=1)

    return (
        Window(label="Year", start=year_start, end=year_end),
        Window(label="Year", start=prev_start, end=prev_end),
    )
