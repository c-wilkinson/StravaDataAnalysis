"""
Utilities for chart styling or other shared visualisation helpers.
"""

import calendar
from dataclasses import dataclass
import datetime
from typing import Callable, Optional, Tuple, List

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.text import Text
import numpy as np
import pandas as pd

DOB = datetime.datetime(1985, 1, 26)


@dataclass(frozen=True)
class TitleBoxConfig:
    """Configuration for the title + attribution banner box."""

    attribution: Optional[str] = "Data sourced from Garmin (synced via Strava)"
    fontsizes: Tuple[int, int] = (14, 9)  # (title_fontsize, subtitle_fontsize)
    offsets: Tuple[float, float] = (0.03, 1.3)  # (top_offset, line_height_scale)
    gap_and_pad: Tuple[float, float] = (0.02, 0.006)  # (min_gap, box_pad)
    box_lr: Tuple[float, float] = (0.05, 0.95)  # (box_left, box_right)


def _occupied_content_top(fig: plt.Figure, renderer) -> float:
    """
    Highest occupied y in figure coords considering axes *tight* bboxes
    (includes tick labels/rotations) and any visible legends.
    Falls back to _axes_top(fig) if nothing measurable is found.
    """
    tops: List[float] = []
    try:
        inv = fig.transFigure.inverted()
    except (AttributeError, ValueError):
        inv = None

    for axis in getattr(fig, "axes", []):
        try:
            if not axis.get_visible():
                continue
        except (AttributeError, ValueError):
            pass

        # Axes tight bbox (ticks/labels included)
        try:
            tight_bbox = axis.get_tightbbox(renderer)
            if tight_bbox is not None:
                tops.append(tight_bbox.transformed(inv).y1 if inv is not None else tight_bbox.y1)
        except (AttributeError, ValueError):
            pass

        # Legend bbox (if present)
        try:
            legend = axis.get_legend()
            if legend is not None and legend.get_visible():
                legend_bbox = legend.get_window_extent(renderer=renderer)
                if legend_bbox is not None:
                    tops.append(
                        legend_bbox.transformed(inv).y1 if inv is not None else legend_bbox.y1
                    )
        except (AttributeError, ValueError):
            pass

    return max(tops) if tops else _axes_top(fig)


def _reserve_space_above_axes(
    fig: plt.Figure, top_limit: float, *, min_bottom: float = 0.05
) -> None:
    """
    Ensure no axes extend above top_limit (figure coords).
    Prefer shifting axes down; if that would push the bottom below min_bottom,
    trim from the top instead.
    """
    for axis in fig.axes:
        if not axis.get_visible():
            continue

        pos = axis.get_position()
        if pos.y1 <= top_limit + 1e-6:
            continue

        excess = pos.y1 - top_limit
        new_y0 = pos.y0 - excess
        new_y1 = top_limit

        # If we can't shift without going below min_bottom, shrink from the top
        if new_y0 < min_bottom:
            new_y0 = pos.y0
            new_y1 = top_limit

        axis.set_position([pos.x0, new_y0, pos.width, new_y1 - new_y0])


def _finalise_and_get_renderer(fig: plt.Figure):
    """Draw once so constrained layout is final and return the renderer."""
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _axes_top(fig: plt.Figure) -> float:
    """Top (y1) of the highest visible axes in figure coords."""
    return max(ax.get_position().y1 for ax in fig.axes if ax.get_visible())


def _line_height(fig: plt.Figure, fontsize_pt: int, scale: float) -> float:
    """
    Convert a font size in points to a figure-coordinate line height.

    Args:
        fig: Matplotlib figure.
        fontsize_pt: Font size in points.
        scale: Multiplier to adjust line spacing.

    Returns:
        Line height in figure coordinates.
    """
    fig_h_in = fig.get_size_inches()[1]
    return (fontsize_pt / 72.0) / fig_h_in * scale


def _place_texts(
    fig: plt.Figure,
    title: str,
    attribution: Optional[str],
    *,
    title_y: float,
    subtitle_y: float,
    title_fontsize: int,
    subtitle_fontsize: int,
) -> Tuple[Text, Optional[Text]]:
    """
    Create title and subtitle Text artists at the given y positions.

    Returns:
        Tuple of (title_text, attribution_text_or_None).
    """
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
    """
    Return the vertical span of the given text elements in **figure coordinates**.

    This computes the minimum and maximum y values across all provided text objects
    after transforming their bounding boxes into the figure's coordinate system
    (0–1 in both x and y).

    Returns:
        (ymin, ymax) of all provided text artists.
    """
    y_bounds: List[Tuple[float, float]] = []
    for artist in artists:
        if artist is None:
            continue
        bounding_box = artist.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        y_bounds.append((bounding_box.ymin, bounding_box.ymax))
    ymin = min(b[0] for b in y_bounds)
    ymax = max(b[1] for b in y_bounds)
    return ymin, ymax


def _shift_texts(title_txt: Text, attr_txt: Optional[Text], shift: float) -> None:
    """
    Shift title and attribution texts upward by a given amount.

    Args:
        title_txt: The title Text artist.
        attr_txt: The attribution Text artist (or None).
        shift: Amount to add to Y position in figure coords.
    """
    x_title, y_title = title_txt.get_position()
    title_txt.set_position((x_title, y_title + shift))
    if attr_txt is not None:
        x_attr, y_attr = attr_txt.get_position()
        attr_txt.set_position((x_attr, y_attr + shift))


def _lift_if_needed(
    fig: plt.Figure,
    *,
    min_gap: float,
    box_pad: float,
    title_txt: Text,
    attr_txt: Optional[Text],
) -> Tuple[float, float]:
    """
    Ensure the box bottom clears the axes by min_gap.
    If needed, shift both texts upward (clamped to the figure top).

    Returns:
        (ymin, ymax) of the final text union after any shift.
    """
    # Get a fresh renderer (also ensures layout is finalised)
    renderer = _finalise_and_get_renderer(fig)

    ymin, ymax = _measure_text_bounds(fig, renderer, [title_txt, attr_txt])
    box_bottom = ymin - box_pad
    occupied_top = _occupied_content_top(fig, renderer)

    # Small extra buffer if any legend is visible (avoids near misses)
    extra = 0.0
    for axis in fig.axes:
        legend = axis.get_legend()
        if legend is not None and legend.get_visible():
            extra = 0.01
            break

    required_bottom = occupied_top + (min_gap + extra)
    if box_bottom >= required_bottom:
        return ymin, ymax

    # Need to lift the banner
    shift = required_bottom - box_bottom
    _, y_title = title_txt.get_position()
    max_y = 0.995
    max_shift = max(0.0, max_y - y_title)
    shift = min(shift, max_shift)

    _shift_texts(title_txt, attr_txt, shift)

    fig.canvas.draw()  # re-measure after moving
    renderer = fig.canvas.get_renderer()
    return _measure_text_bounds(fig, renderer, [title_txt, attr_txt])


def _draw_background_box(
    fig: plt.Figure,
    *,
    ymin: float,
    ymax: float,
    box_left: float,
    box_right: float,
    box_pad: float,
) -> None:
    """
    Draw a white rounded rectangle behind the title and subtitle.

    Args:
        fig: Matplotlib figure.
        ymin: Lower y-bound of text union (figure coords).
        ymax: Upper y-bound of text union (figure coords).
        box_left: Left x-position of box (figure coords).
        box_right: Right x-position of box (figure coords).
        box_pad: Padding applied above/below the text union (figure coords).
    """
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


def add_title_with_attribution(
    fig: plt.Figure,
    title: str,
    config: TitleBoxConfig = TitleBoxConfig(),
) -> None:
    """
    Add a title and optional attribution above the plot area, automatically
    lifting them if they would overlap the axes, and drawing a rounded
    background box behind both lines.
    """
    if not fig.axes:
        return

    axes_top = _axes_top(fig)
    subtitle_y = axes_top + config.offsets[0]
    title_y = subtitle_y + _line_height(fig, config.fontsizes[1], config.offsets[1])

    title_txt, attr_txt = _place_texts(
        fig,
        title,
        config.attribution,
        title_y=title_y,
        subtitle_y=subtitle_y,
        title_fontsize=config.fontsizes[0],
        subtitle_fontsize=config.fontsizes[1],
    )

    ymin, ymax = _lift_if_needed(
        fig,
        min_gap=config.gap_and_pad[0],
        box_pad=config.gap_and_pad[1],
        title_txt=title_txt,
        attr_txt=attr_txt,
    )

    # Push axes down so they clear the banner by at least min_gap
    header_bottom = ymin - config.gap_and_pad[1]
    top_limit = header_bottom - config.gap_and_pad[0]
    _reserve_space_above_axes(fig, top_limit)
    fig.canvas.draw()

    _draw_background_box(
        fig,
        ymin=ymin,
        ymax=ymax,
        box_left=config.box_lr[0],
        box_right=config.box_lr[1],
        box_pad=config.gap_and_pad[1],
    )


def configure_matplotlib_styles() -> None:
    """
    Apply consistent style settings across all charts.
    """
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["legend.fontsize"] = 12
    plt.rcParams["axes.grid"] = True


def format_pace(value: float, _) -> str:
    """
    Convert a time value in seconds into 'minutes:seconds' format.
    """
    if not np.isfinite(value):
        return ""
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes}:{seconds:02d}"


def classify_zone_dynamic(heart_rate: float, date_str: str) -> str:
    """
    Classify heart rate into a dynamic training zone based on age at the run date.

    Zones are computed from a max HR of (220 - age) on the given date.
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
    Aggregate and derive per-run pace metrics from individual split data.

    Adds:
        - pace_sec_km: seconds per kilometre for the run
        - distance_km, pace_sec, year
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
    Clean and enrich raw activities data for plotting time vs. distance trends.

    Adds:
        - distance_km, time_seconds, year, is_last_run
      and filters out very short activities (< 0.5 km).
    """
    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[data["distance_km"] >= 0.5]
    data["time_seconds"] = data["moving_time_s"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    last_run_date = pd.to_datetime(data["start_date_local"]).max()
    data["is_last_run"] = pd.to_datetime(data["start_date_local"]) == last_run_date
    return data


def calculate_decay_point(data: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute an extrapolated decay point for visualising projected pacing trends.

    Returns:
        (decay_distance_km, decay_time_seconds)
    """
    max_distance = data["distance_km"].max()
    max_time = data["time_seconds"].max()
    decay_distance = max_distance + 2
    average_pace = max_time / max_distance
    decay_time = decay_distance * (average_pace + 180)
    return decay_distance, decay_time


def seconds_to_hms(value, _):
    """
    Convert a numeric value (in seconds) to a HH:MM:SS formatted string.
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
    Add 'year' and 'month' columns based on 'start_date_local'.
    """
    data = dataframe.copy()
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month
    return data


def prepare_activities_with_distance(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Copy and derive 'distance_km', 'year', 'month' from raw activities.
    """
    if activities_df.empty:
        return pd.DataFrame()

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = extract_year_month(data)
    return data


def prepare_1km_splits(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter splits to ~1 km and add 'distance_km' and 'year'.
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

    Args:
        title: Figure title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        output_path: File path to save the figure.
        plot_func: Callable that accepts a Matplotlib axis and draws the plot.
        attribution: Optional attribution text for data source.
        figsize: Figure size in inches (width, height).
    """
    fig, axis = plt.subplots(figsize=figsize, constrained_layout=True)
    plot_func(axis)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True)
    add_title_with_attribution(
        fig,
        title,
        TitleBoxConfig(attribution=attribution),
    )
    save_and_close_plot(output_path)


def prepare_dated_activities(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare an activities DataFrame for time series plotting.

    Adds a sorted 'start_date' timestamp column.
    """
    if activities_df.empty:
        return pd.DataFrame()
    data = prepare_activities_with_distance(activities_df)
    data["start_date"] = pd.to_datetime(data["start_date_local"])
    return data.sort_values("start_date")


def label_month_axis(axis):
    """
    Apply consistent x-axis formatting for month-based plots.
    """
    axis.set_xticks(range(1, 13))
    axis.set_xticklabels(calendar.month_abbr[1:13], rotation=45)


def label_month_axis_barplot(axis):
    """
    Apply consistent x-axis formatting for month-based (bar) plots.
    """
    axis.set_xticks(np.arange(12) + 0.5)
    axis.set_xticklabels(calendar.month_abbr[1:13], rotation=45)
