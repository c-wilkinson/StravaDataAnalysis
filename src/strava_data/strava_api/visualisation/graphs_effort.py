"""
Contains the effort chart functions, each saving a PNG file.
"""

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation import utils


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
