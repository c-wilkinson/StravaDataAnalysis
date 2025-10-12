"""
Utilities for chart styling or other shared visualisation helpers.
"""

import calendar
import datetime
from typing import Callable, Optional, Tuple, List

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.text import Text
import numpy as np
import pandas as pd

DOB = datetime.datetime(1985, 1, 26)


def _finalise_and_get_renderer(fig: plt.Figure):
    """Draw once so constrained layout is final and return the renderer."""
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _axes_top(fig: plt.Figure) -> float:
    """Top (y1) of the highest visible axes in figure coords."""
    return max(ax.get_position().y1 for ax in fig.axes if ax.get_visible())


def _line_height(fig: plt.Figure, fontsize_pt: int, scale: float) -> float:
    """Convert a font size in points to a figure-coordinate line height."""
    fig_h_in = fig.get_size_inches()[1]
    return (fontsize_pt / 72.0) / fig_h_in * scale


def _place_texts(
    fig: plt.Figure,
    title: str,
    attribution: Optional[str],
    title_y: float,
    subtitle_y: float,
    title_fontsize: int,
    subtitle_fontsize: int,
) -> Tuple[Text, Optional[Text]]:
    """Create title and subtitle Text artists at the given y positions."""
    title_txt = fig.text(
        0.5,
        title_y,
        title,
        ha="center",
        va="bottom",
        fontsize=title_fontsize,
        color="black",
        zorder=3,
    )
    attr_txt = None
    if attribution:
        attr_txt = fig.text(
            0.5,
            subtitle_y,
            attribution,
            ha="center",
            va="bottom",
            fontsize=subtitle_fontsize,
            color="gray",
            zorder=3,
        )
    return title_txt, attr_txt


def _measure_text_bounds(fig: plt.Figure, renderer, artists: List[Text]) -> Tuple[float, float]:
    """Union of artists' vertical bounds in figure coords."""
    ys = []
    for art in artists:
        if art is None:
            continue
        bb = art.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        ys.append((bb.ymin, bb.ymax))
    ymin = min(y[0] for y in ys)
    ymax = max(y[1] for y in ys)
    return ymin, ymax


def _lift_if_needed(
    fig: plt.Figure,
    renderer,
    axes_top: float,
    min_gap: float,
    box_pad: float,
    title_txt: Text,
    attr_txt: Optional[Text],
) -> Tuple[float, float]:
    """
    Ensure the box bottom clears the axes by min_gap.
    If needed, shift both texts upward (clamped to the figure top).
    Returns (ymin, ymax) of the final text union.
    """
    ymin, ymax = _measure_text_bounds(fig, renderer, [title_txt, attr_txt])
    box_bottom = ymin - box_pad
    required_bottom = axes_top + min_gap
    if box_bottom >= required_bottom:
        return ymin, ymax

    # Need to lift the banner
    shift = required_bottom - box_bottom
    x_t, y_t = title_txt.get_position()
    max_y = 0.995
    max_shift = max(0.0, max_y - y_t)
    shift = min(shift, max_shift)

    title_txt.set_position((x_t, y_t + shift))
    if attr_txt is not None:
        x_a, y_a = attr_txt.get_position()
        attr_txt.set_position((x_a, y_a + shift))

    fig.canvas.draw()  # re-measure after moving
    return _measure_text_bounds(fig, fig.canvas.get_renderer(), [title_txt, attr_txt])


def add_title_with_attribution(
    fig: plt.Figure,
    title: str,
    *,
    attribution: Optional[str] = "Data sourced from Garmin (synced via Strava)",
    title_fontsize: int = 14,
    subtitle_fontsize: int = 9,
    top_offset: float = 0.03,
    line_height_scale: float = 1.3,
    min_gap: float = 0.02,
    box_pad: float = 0.006,
    box_left: float = 0.05,
    box_right: float = 0.95,
) -> None:
    """
    Add a title and optional attribution above the plot area.
    """
    if not fig.axes:
        return

    renderer = _finalise_and_get_renderer(fig)
    axes_top = _axes_top(fig)
    subtitle_y = axes_top + top_offset
    title_y = subtitle_y + _line_height(fig, subtitle_fontsize, line_height_scale)

    # Create texts
    title_txt, attr_txt = _place_texts(
        fig, title, attribution, title_y, subtitle_y, title_fontsize, subtitle_fontsize
    )

    # Lift if needed so the box clears the axes
    ymin, ymax = _lift_if_needed(fig, renderer, axes_top, min_gap, box_pad, title_txt, attr_txt)

    # Draw one white rounded rectangle behind both lines
    fig.patches.append(
        FancyBboxPatch(
            (box_left, ymin - box_pad),
            (box_right - box_left),
            (ymax - ymin) + 2 * box_pad,
            transform=fig.transFigure,
            boxstyle="round,pad=0.004,rounding_size=0.01",
            facecolor="white",
            edgecolor="lightgray",
            linewidth=0.8,
            alpha=0.95,
            zorder=2,
        )
    )


def configure_matplotlib_styles() -> None:
    """
    Applies consistent style settings across all charts.
    """
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["legend.fontsize"] = 12
    plt.rcParams["axes.grid"] = True


def format_pace(value: float, _) -> str:
    """
    Converts a time value in seconds into 'minutes:seconds' format.
    """
    if not np.isfinite(value):
        return ""
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes}:{seconds:02d}"


def classify_zone_dynamic(heart_rate: float, date_str: str) -> str:
    """
    Classifies heart rate into a dynamic training zone based on age at the run date.
    """
    try:
        run_date = pd.to_datetime(date_str)
    except (ValueError, TypeError):
        return "Unknown"

    age = run_date.year - DOB.year - ((run_date.month, run_date.day) < (DOB.month, DOB.day))
    max_hr = 220 - age
    heart_pct = heart_rate / max_hr

    if heart_pct < 0.60:
        return "Z1 (<60%)"
    if heart_pct < 0.70:
        return "Z2 (60–70%)"
    if heart_pct < 0.80:
        return "Z3 (70–80%)"
    if heart_pct < 0.90:
        return "Z4 (80–90%)"
    return "Z5 (90–100%)"


def prepare_pace_distance_data(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates and derives per-run pace metrics from individual split data.
    """
    splits = splits_df.copy()
    splits["pace_sec_km"] = splits["elapsed_time_s"] / (splits["distance_m"] / 1000)
    grouped_df = (
        splits.groupby(["activity_id", "start_date_local"])
        .agg({"distance_m": "sum", "elapsed_time_s": "sum"})
        .reset_index()
    )
    grouped_df["pace_sec_km"] = grouped_df["elapsed_time_s"] / (grouped_df["distance_m"] / 1000)
    grouped_df["distance_km"] = grouped_df["distance_m"] / 1000
    grouped_df["pace_sec"] = grouped_df["pace_sec_km"]
    grouped_df["year"] = pd.to_datetime(grouped_df["start_date_local"]).dt.year
    return grouped_df


def prepare_time_distance_data(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches raw activities data for plotting time vs. distance trends.
    """
    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[data["distance_km"] >= 0.5]
    data["time_seconds"] = data["moving_time_s"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    last_run_date = pd.to_datetime(data["start_date_local"]).max()
    data["is_last_run"] = pd.to_datetime(data["start_date_local"]) == last_run_date
    return data


def calculate_decay_point(data: pd.DataFrame) -> tuple[float, float]:
    """
    Computes an extrapolated decay point for visualizing projected pacing trends.
    """
    max_distance = data["distance_km"].max()
    max_time = data["time_seconds"].max()
    decay_distance = max_distance + 2
    average_pace = max_time / max_distance
    decay_time = decay_distance * (average_pace + 180)
    return decay_distance, decay_time


def seconds_to_hms(value, _):
    """
    Converts a numeric value (in seconds) to a HH:MM:SS formatted string.
    """
    return str(datetime.timedelta(seconds=int(value)))


def save_and_close_plot(output_path: str) -> None:
    """
    Common helper to save matplotlib plots without switching layout engines.
    """
    fig = plt.gcf()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def extract_year_month(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'year' and 'month' columns based on 'start_date_local'.
    """
    data = dataframe.copy()
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month
    return data


def prepare_activities_with_distance(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Copies and derives 'distance_km', 'year', 'month' from raw activities.
    """
    if activities_df.empty:
        return pd.DataFrame()

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = extract_year_month(data)
    return data


def prepare_1km_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters splits to ~1 km and adds 'distance_km' and 'year'.
    """
    if splits_df.empty:
        return pd.DataFrame()

    data = splits_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[(data["distance_km"] >= 0.95) & (data["distance_km"] <= 1.05)]
    if data.empty:
        return pd.DataFrame()

    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    return data


def plot_with_common_setup(
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: str,
    plot_func: Callable,
    *,
    attribution: Optional[str] = "Data sourced from Garmin (synced via Strava)",
    figsize: tuple[int, int] = (10, 5),
):
    """
    Reusable wrapper to set up common plot structure and call the provided plot_func.
    """
    fig, axis = plt.subplots(figsize=figsize, constrained_layout=True)
    plot_func(axis)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True)
    add_title_with_attribution(fig, title, attribution=attribution)
    save_and_close_plot(output_path)


def prepare_dated_activities(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares an activities DataFrame for time series plotting.
    """
    if activities_df.empty:
        return pd.DataFrame()
    data = prepare_activities_with_distance(activities_df)
    data["start_date"] = pd.to_datetime(data["start_date_local"])
    return data.sort_values("start_date")


def label_month_axis(axis):
    """
    Applies consistent x-axis formatting for month-based plots.
    """
    axis.set_xticks(range(1, 13))
    axis.set_xticklabels(calendar.month_abbr[1:13], rotation=45)


def label_month_axis_barplot(axis):
    """
    Applies consistent x-axis formatting for month-based (bar) plots.
    """
    axis.set_xticks(np.arange(12) + 0.5)
    axis.set_xticklabels(calendar.month_abbr[1:13], rotation=45)
