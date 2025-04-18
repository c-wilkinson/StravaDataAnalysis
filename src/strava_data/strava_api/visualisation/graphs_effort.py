"""
Contains the effort chart functions, each saving a PNG file.
"""

import calendar

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
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
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    monthly_stats = (
        data.groupby(["year", "month"])
        .agg({"distance_km": "sum", "total_elevation_gain_m": "sum"})
        .reset_index()
    )

    # Avoid division by zero
    monthly_stats = monthly_stats[monthly_stats["distance_km"] > 0]
    monthly_stats["elev_gain_per_km"] = (
        monthly_stats["total_elevation_gain_m"] / monthly_stats["distance_km"]
    )

    plt.figure()
    for year in sorted(monthly_stats["year"].unique()):
        year_data = monthly_stats[monthly_stats["year"] == year].sort_values("month")
        plt.plot(year_data["month"], year_data["elev_gain_per_km"], marker="o", label=str(year))

    plt.title("Elevation Gain per km by Month")
    plt.xlabel("Month")
    plt.ylabel("Elevation Gain (m/km)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13])
    plt.legend(title="Year")
    utils.save_and_close_plot(output_path)


def plot_cadence_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Scatter plot of average cadence over time with trend line.
    - Filters to activities with cadence > 0
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["start_date"] = pd.to_datetime(data["start_date_local"])
    data = data[data["average_cadence"] > 0].sort_values("start_date")

    if data.empty:
        return

    data["start_date_num"] = mdates.date2num(data["start_date"])

    plt.figure()
    axis = plt.gca()

    # Scatter plot
    sns.scatterplot(data=data, x="start_date", y="average_cadence", alpha=0.5, ax=axis)

    # Trend line
    sns.regplot(
        data=data,
        x="start_date_num",
        y="average_cadence",
        scatter=False,
        color="black",
        line_kws={"linestyle": "--"},
        ax=axis,
    )

    plt.title("Average Cadence Over Time")
    plt.xlabel("Date")
    plt.ylabel("Cadence (steps per minute)")
    plt.xticks(rotation=45)
    utils.save_and_close_plot(output_path)


def plot_effort_score_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Line plot showing calculated effort score over time.
    effort = (distance_km * 10) + (elevation_gain_m * 1.5)
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["start_date"] = pd.to_datetime(data["start_date_local"])
    data = data.sort_values("start_date")

    data["distance_km"] = data["distance_m"] / 1000.0
    data["effort_score"] = (data["distance_km"] * 10) + (data["total_elevation_gain_m"] * 1.5)

    # Smooth with a rolling 7-day window to reduce noise
    data["rolling_effort"] = data["effort_score"].rolling(window=7).mean()

    plt.figure()
    plt.plot(data["start_date"], data["rolling_effort"], label="7-day Avg Effort", color="blue")
    plt.title("Training Load (Effort Score) Over Time")
    plt.xlabel("Date")
    plt.ylabel("Effort Score")
    plt.grid(True)
    plt.legend()
    utils.save_and_close_plot(output_path)


def plot_vo2_proxy_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Estimates a VO₂ max–style fitness proxy using 1 km split pace over time.

    VO₂ proxy = 15.0 × (speed in m/s), where speed = distance / time for fastest split per month.

    Produces a line chart per year showing how top-end aerobic fitness changes across months.
    """
    if splits_df.empty:
        return

    data = splits_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0

    # Focus on ~1 km splits
    data = data[(data["distance_km"] >= 0.95) & (data["distance_km"] <= 1.05)]
    if data.empty:
        return

    data["pace_sec_km"] = data["elapsed_time_s"] / data["distance_km"]
    data["speed_mps"] = data["distance_m"] / data["elapsed_time_s"]
    data["vo2_proxy"] = 15.0 * data["speed_mps"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    # Get fastest (highest VO2 proxy) split per month per year
    monthly = data.groupby(["year", "month"])["vo2_proxy"].max().reset_index()

    # Ensure we have all months filled (fill missing months with NaN)
    rows = []
    for year in sorted(monthly["year"].unique()):
        for month in range(1, 13):
            match = monthly[(monthly["year"] == year) & (monthly["month"] == month)]
            value = match["vo2_proxy"].values[0] if not match.empty else np.nan
            rows.append({"year": year, "month": month, "vo2_proxy": value})
    plot_df = pd.DataFrame(rows)
    plot_df["vo2_proxy"] = plot_df.groupby("year")["vo2_proxy"].ffill()

    # Plotting
    plt.figure()
    for year in sorted(plot_df["year"].unique()):
        sub = plot_df[plot_df["year"] == year]
        plt.plot(sub["month"], sub["vo2_proxy"], marker="o", label=str(year))

    plt.title("Estimated VO₂ Max Proxy Over Time")
    plt.xlabel("Month")
    plt.ylabel("VO₂ Proxy")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.legend(title="Year")
    plt.grid(True)
    utils.save_and_close_plot(output_path)
