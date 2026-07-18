"""Formatting helpers for Streamlit metrics and tables."""

from __future__ import annotations

import math

import pandas as pd

from strava_data.strava_api.visualisation.interactive_utils import (
    format_pace as format_interactive_pace,
)


def format_duration(seconds: float | int) -> str:
    """Format seconds as a compact hours and minutes duration."""
    if seconds is None or not math.isfinite(float(seconds)):
        return "—"
    total_minutes = int(round(float(seconds) / 60.0))
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def format_pace(seconds_per_km: float | int) -> str:
    """Format seconds per kilometre as minutes and seconds."""
    return format_interactive_pace(seconds_per_km)


def rounded_numeric(
    values: pd.Series, decimals: int = 0, *, zero_as_missing: bool = False
) -> pd.Series:
    """Return a nullable rounded numeric series, safely handling ``NaT`` values."""
    clean_values = values.astype("object").where(values.notna(), None)
    numeric_values = pd.to_numeric(clean_values, errors="coerce").astype("Float64")
    if zero_as_missing:
        numeric_values = numeric_values.mask(numeric_values.eq(0))
    return numeric_values.round(decimals)
