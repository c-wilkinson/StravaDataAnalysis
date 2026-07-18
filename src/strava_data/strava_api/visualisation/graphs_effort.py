"""
Contains the effort chart functions, each saving a PNG file.
"""

# pylint: disable=duplicate-code

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

from strava_data.strava_api.processing.analytics import (
    monthly_elevation_per_km,
    monthly_vo2_proxy,
    prepare_activities,
    training_load,
)
from strava_data.strava_api.visualisation import interactive_utils, utils


def plot_elevation_gain_per_km_by_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots average elevation gain per km for each month, per year.
    - X-axis: Month (Jan–Dec)
    - Y-axis: Elevation gain per km
    - Line series: one per year
    """
    data = utils.prepare_dated_activities(activities_df)

    monthly_stats = (
        data.groupby(["year", "month"])
        .agg({"distance_km": "sum", "total_elevation_gain_m": "sum"})
        .reset_index()
    )

    monthly_stats = monthly_stats[monthly_stats["distance_km"] > 0]
    monthly_stats["elev_gain_per_km"] = (
        monthly_stats["total_elevation_gain_m"] / monthly_stats["distance_km"]
    )

    def plot_fn(axis):
        for year in sorted(monthly_stats["year"].unique()):
            year_data = monthly_stats[monthly_stats["year"] == year].sort_values("month")
            axis.plot(
                year_data["month"], year_data["elev_gain_per_km"], marker="o", label=str(year)
            )
        utils.label_month_axis(axis)
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Elevation Gain per km by Month",
        xlabel="Month",
        ylabel="Elevation Gain (m/km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_cadence_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Scatter plot of average cadence over time with trend line.
    - Filters to activities with cadence > 0
    """
    data = utils.prepare_dated_activities(activities_df)
    data = data[data["average_cadence"] > 0]
    if data.empty:
        return

    data["start_date"] = pd.to_datetime(data["start_date_local"])
    data = data.sort_values("start_date")
    data["start_date_num"] = mdates.date2num(data["start_date"])

    def plot_fn(axis):
        sns.scatterplot(data=data, x="start_date", y="average_cadence", alpha=0.5, ax=axis)
        sns.regplot(
            data=data,
            x="start_date_num",
            y="average_cadence",
            scatter=False,
            color="black",
            line_kws={"linestyle": "--"},
            ax=axis,
        )
        for label in axis.get_xticklabels():
            label.set_rotation(45)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Average Cadence Over Time",
        xlabel="Date",
        ylabel="Cadence (steps per minute)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_effort_score_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Line plot showing calculated effort score over time.
    effort = (distance_km * 10) + (elevation_gain_m * 1.5)
    """
    data = utils.prepare_dated_activities(activities_df)
    data["effort_score"] = (data["distance_km"] * 10) + (data["total_elevation_gain_m"] * 1.5)
    data["rolling_effort"] = data["effort_score"].rolling(window=7).mean()

    def plot_fn(axis):
        axis.plot(
            data["start_date"], data["rolling_effort"], label="7-day Avg Effort", color="blue"
        )
        axis.legend()
        axis.grid(True)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Training Load (Effort Score) Over Time",
        xlabel="Date",
        ylabel="Effort Score",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_vo2_proxy_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Estimates a VO₂ max–style fitness proxy using 1 km split pace over time.

    VO₂ proxy = 15.0 × (speed in m/s), where speed = distance / time for fastest split per month.

    Produces a line chart per year showing how top-end aerobic fitness changes across months.
    """
    data = utils.prepare_dated_activities(splits_df)
    if data.empty:
        return

    data["pace_sec_km"] = data["elapsed_time_s"] / data["distance_km"]
    data["speed_mps"] = data["distance_m"] / data["elapsed_time_s"]
    data["vo2_proxy"] = 15.0 * data["speed_mps"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    monthly = data.groupby(["year", "month"])["vo2_proxy"].max().reset_index()

    rows = []
    for year in sorted(monthly["year"].unique()):
        for month in range(1, 13):
            match = monthly[(monthly["year"] == year) & (monthly["month"] == month)]
            value = match["vo2_proxy"].values[0] if not match.empty else np.nan
            rows.append({"year": year, "month": month, "vo2_proxy": value})

    plot_df = pd.DataFrame(rows)
    plot_df["vo2_proxy"] = plot_df.groupby("year")["vo2_proxy"].ffill()

    def plot_fn(axis):
        for year in sorted(plot_df["year"].unique()):
            sub = plot_df[plot_df["year"] == year]
            axis.plot(sub["month"], sub["vo2_proxy"], marker="o", label=str(year))
        utils.label_month_axis(axis)
        axis.legend(title="Year")
        axis.grid(True)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Estimated VO₂ Max Proxy Over Time",
        xlabel="Month",
        ylabel="VO₂ Proxy",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def build_cadence_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive average cadence chart."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()
    data = data[data["average_cadence"] > 0]
    figure = px.scatter(
        data,
        x="activity_date",
        y="average_cadence",
        hover_name="name",
        labels={"activity_date": "Date", "average_cadence": "Cadence"},
        hover_data={"activity_date": "|%d %B %Y", "distance_km": ":.2f"},
    )
    interactive_utils.add_linear_trend(figure, data["activity_date"], data["average_cadence"])
    return interactive_utils.apply_layout(figure, "Average cadence over time", "Cadence")


def build_elevation_per_km_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive elevation-gain-per-kilometre chart."""
    data = monthly_elevation_per_km(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="month_start",
        y="elevation_per_km",
        markers=True,
        labels={"month_start": "Month", "elevation_per_km": "Elevation gain (m/km)"},
        hover_data={"month_start": "|%B %Y", "elevation_per_km": ":.1f"},
    )
    return interactive_utils.apply_layout(
        figure, "Elevation gain per km by month", "Elevation gain (m/km)"
    )


def build_training_load_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive training-load chart."""
    data = training_load(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="activity_date",
        y="rolling_effort",
        labels={"activity_date": "Date", "rolling_effort": "Effort score"},
        hover_name="name",
        hover_data={"effort_score": ":.1f", "rolling_effort": ":.1f"},
    )
    return interactive_utils.apply_layout(
        figure, "Training load over time", "Seven-activity average effort"
    )


def build_vo2_proxy_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive version of the VO2 proxy chart."""
    data = monthly_vo2_proxy(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="month_start",
        y="vo2_proxy",
        markers=True,
        labels={"month_start": "Month", "vo2_proxy": "VO₂ proxy"},
        hover_data={"month_start": "|%B %Y", "vo2_proxy": ":.1f"},
    )
    return interactive_utils.apply_layout(figure, "Estimated VO₂ proxy over time", "VO₂ proxy")
