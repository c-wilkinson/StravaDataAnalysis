"""Shared helpers for Plotly versions of the existing Strava charts."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def format_pace(seconds_per_km: float | int) -> str:
    """Format seconds per kilometre as minutes and seconds."""
    if seconds_per_km is None or not math.isfinite(float(seconds_per_km)):
        return "—"
    total_seconds = int(round(float(seconds_per_km)))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}/km"


def pace_tick_values(values: pd.Series, count: int = 7) -> tuple[list[float], list[str]]:
    """Build readable mm:ss Plotly axis ticks for a numeric pace series."""
    clean = pd.to_numeric(values, errors="coerce").dropna()
    clean = clean[clean.map(math.isfinite)]
    if clean.empty:
        return [], []
    lower = max(0, int(clean.min() // 30) * 30)
    upper = int(math.ceil(clean.max() / 30.0) * 30)
    if lower == upper:
        upper += 30
    raw_step = (upper - lower) / max(count - 1, 1)
    step = max(30, int(math.ceil(raw_step / 30.0) * 30))
    ticks = list(range(lower, upper + step, step))
    labels = [format_pace(value).replace("/km", "") for value in ticks]
    return ticks, labels


def apply_layout(figure: go.Figure, title: str, y_title: str = "") -> go.Figure:
    """Apply the common interactive-chart layout."""
    figure.update_layout(
        title=title,
        hovermode="closest",
        legend_title_text="",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    if y_title:
        figure.update_yaxes(title_text=y_title)
    return figure


def apply_pace_axis(
    figure: go.Figure, values: pd.Series, title: str = "Pace (min/km)"
) -> go.Figure:
    """Format a Plotly y-axis containing pace in seconds per kilometre."""
    tick_values, tick_text = pace_tick_values(values)
    figure.update_yaxes(title_text=title, tickvals=tick_values, ticktext=tick_text)
    return figure


def add_linear_trend(
    figure: go.Figure,
    x_values: pd.Series,
    y_values: pd.Series,
    name: str = "Trend",
) -> go.Figure:
    """Add a least-squares trend line when enough valid values are present."""
    clean = pd.DataFrame({"x": x_values, "y": y_values}).dropna()
    if len(clean) < 3:
        return figure
    if pd.api.types.is_datetime64_any_dtype(clean["x"]):
        numeric_x = clean["x"].astype("int64") / 1_000_000_000
    else:
        numeric_x = pd.to_numeric(clean["x"], errors="coerce")
    numeric_y = pd.to_numeric(clean["y"], errors="coerce")
    valid = numeric_x.notna() & numeric_y.notna()
    clean = clean.loc[valid].copy()
    numeric_x = numeric_x.loc[valid]
    numeric_y = numeric_y.loc[valid]
    if len(clean) < 3 or numeric_x.nunique() < 2:
        return figure
    coefficients = np.polyfit(numeric_x, numeric_y, 1)
    clean["trend"] = np.polyval(coefficients, numeric_x)
    clean = clean.sort_values("x")
    figure.add_trace(
        go.Scatter(
            x=clean["x"],
            y=clean["trend"],
            mode="lines",
            name=name,
            line={"dash": "dash"},
            hoverinfo="skip",
        )
    )
    return figure
