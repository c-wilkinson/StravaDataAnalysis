"""
Contains the distribution chart functions, each saving a PNG file.
"""

import calendar

from matplotlib import ticker
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation import utils


def plot_run_distance_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plot showing distribution of run distances, split by year.
    Highlights distance preferences and training evolution over time.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year

    plt.figure()
    axis = plt.gca()

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year]
        if year_data["distance_km"].nunique() > 1:
            sns.kdeplot(year_data["distance_km"], fill=True, label=str(year), alpha=0.3, ax=axis)

    axis.set_xlim(left=0)
    axis.set_title("Run Distance Distribution by Year")
    axis.set_xlabel("Distance (km)")
    axis.set_ylabel("Density")
    plt.legend(title="Year")
    plt.grid(True, linestyle="--", linewidth=0.5)
    utils.save_and_close_plot(output_path)


def plot_pace_distribution(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plot showing distribution of paces (in mm:ss per km), one per year.
    Only includes ~1 km splits.
    """
    if splits_df.empty:
        return

    data = splits_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[(data["distance_km"] >= 0.95) & (data["distance_km"] <= 1.05)]
    if data.empty:
        return

    data["pace_sec_km"] = data["elapsed_time_s"] / data["distance_km"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year

    plt.figure()
    axis = plt.gca()

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year]
        if year_data["pace_sec_km"].nunique() > 1:
            sns.kdeplot(year_data["pace_sec_km"], fill=True, label=str(year), alpha=0.3, ax=axis)

    axis.xaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    axis.set_title("Pace Distribution by Year (1 km splits)")
    axis.set_xlabel("Pace (mm:ss)")
    axis.set_ylabel("Density")
    plt.legend(title="Year")
    plt.grid(True)
    utils.save_and_close_plot(output_path)


def plot_elevation_gain_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plots showing distribution of elevation gain per run, one per year.
    Highlights how hilly your training was year-to-year.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["elevation_gain"] = data["total_elevation_gain_m"]
    data = data[data["elevation_gain"] != 0]  # Filter out treadmill runs
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year

    plt.figure()
    axis = plt.gca()

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year]
        if year_data["elevation_gain"].nunique() > 1:
            sns.kdeplot(year_data["elevation_gain"], fill=True, label=str(year), alpha=0.3, ax=axis)

    axis.set_title("Elevation Gain per Run (by Year)")
    axis.set_xlabel("Elevation Gain (m)")
    axis.set_ylabel("Density")
    plt.legend(title="Year")
    plt.grid(True, linestyle="--", linewidth=0.5)
    utils.save_and_close_plot(output_path)


def plot_heart_rate_zone_distribution(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Stacked bar chart showing time spent in heart rate zones per month.
    Only includes ~1 km splits with valid heart rate data.
    """
    if splits_df.empty:
        return

    data = splits_df.copy()
    data = data[(data["distance_m"] >= 950) & (data["distance_m"] <= 1050)]
    data = data[pd.notnull(data["average_heartrate"])]

    if data.empty:
        return

    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month
    data["month_label"] = data["year"].astype(str) + "-" + data["month"].astype(str).str.zfill(2)
    data["hr_zone"] = data.apply(
        lambda row: utils.classify_zone_dynamic(row["average_heartrate"], row["start_date_local"]),
        axis=1,
    )

    # Total time spent per zone per month
    data["time_min"] = data["elapsed_time_s"] / 60.0
    grouped = data.groupby(["month_label", "hr_zone"])["time_min"].sum().unstack().fillna(0)

    # Plot
    grouped = grouped.sort_index()
    grouped.plot(kind="bar", stacked=True, figsize=(14, 6), colormap="viridis")

    plt.title("Training Intensity by Heart Rate Zone")
    plt.xlabel("Month")
    plt.ylabel("Time Spent (minutes)")
    plt.xticks(rotation=45)
    plt.legend(title="Heart Rate Zone")
    utils.save_and_close_plot(output_path)


def plot_run_start_time_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Box plot showing distribution of run start times by month.
    - X-axis: Month (Jan–Dec)
    - Y-axis: Hour of day (0–23)
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["start_time"] = pd.to_datetime(data["start_date_local"], errors="coerce")
    data["month"] = data["start_time"].dt.month
    data["hour"] = data["start_time"].dt.hour

    if data[["month", "hour"]].dropna().empty:
        return

    plt.figure()
    sns.boxplot(data=data, x="month", y="hour")
    plt.title("Distribution of Run Start Time by Month")
    plt.xlabel("Month")
    plt.ylabel("Start Hour of Day")
    plt.xticks(ticks=range(0, 12), labels=calendar.month_abbr[1:13])
    utils.save_and_close_plot(output_path)


def plot_run_days_heatmap(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap showing number of days with runs per month.
    Highlights how consistently you trained.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["date"] = pd.to_datetime(data["start_date_local"]).dt.date
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    # Count unique run dates per month
    run_days = data.drop_duplicates(subset="date")
    summary = run_days.groupby(["year", "month"]).size().reset_index(name="run_day_count")
    pivot = summary.pivot(index="year", columns="month", values="run_day_count")

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        pivot,
        annot=pivot.notna(),  # Only annotate cells with data
        fmt=".0f",
        cmap="Greens",
        cbar_kws={"label": "Run Days"},
        mask=pivot.isna(),  # Hide non-existent cells
    )
    plt.title("Run Days per Month")
    plt.xlabel("Month")
    plt.ylabel("Year")
    plt.xticks(ticks=np.arange(12) + 0.5, labels=calendar.month_abbr[1:13], rotation=45)
    utils.save_and_close_plot(output_path)


def plot_rest_days_heatmap(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap showing number of rest days per month.
    Only annotates months where rest days occurred.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["date"] = pd.to_datetime(data["start_date_local"]).dt.date

    # Build full date range from first to last activity
    start = data["date"].min()
    end = data["date"].max()
    full_dates = pd.DataFrame({"date": [d.date() for d in pd.date_range(start, end)]})

    # Identify rest days
    rest_days = full_dates[~full_dates["date"].isin(data["date"])].copy()
    rest_days["year"] = pd.to_datetime(rest_days["date"]).dt.year
    rest_days["month"] = pd.to_datetime(rest_days["date"]).dt.month

    rest_summary = rest_days.groupby(["year", "month"]).size().reset_index(name="rest_day_count")
    pivot = rest_summary.pivot(index="year", columns="month", values="rest_day_count")

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        pivot,
        annot=pivot.notna(),  # Only annotate cells with data
        fmt=".0f",
        cmap="Reds",
        cbar_kws={"label": "Rest Days"},
        mask=pivot.isna(),  # Hide non-existent cells
    )
    plt.title("Rest Days per Month")
    plt.xlabel("Month")
    plt.ylabel("Year")
    plt.xticks(ticks=np.arange(12) + 0.5, labels=calendar.month_abbr[1:13], rotation=45)
    utils.save_and_close_plot(output_path)


def plot_run_rest_ratio_heatmap(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap showing the run:rest ratio per month with colour-coded zones:
    - Green = Balanced (0.25–0.9)
    - Red = High (overtraining)
    - Yellow = Low (undertraining)
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["date"] = pd.to_datetime(data["start_date_local"]).dt.date

    start = data["date"].min()
    end = data["date"].max()
    all_dates = pd.DataFrame({"date": [d.date() for d in pd.date_range(start, end)]})
    all_dates["year"] = pd.to_datetime(all_dates["date"]).dt.year
    all_dates["month"] = pd.to_datetime(all_dates["date"]).dt.month

    run_dates = data.drop_duplicates(subset="date")[["date"]].copy()
    run_dates["ran"] = 1

    merged = all_dates.merge(run_dates, on="date", how="left")
    merged["ran"] = merged["ran"].fillna(0)

    summary = (
        merged.groupby(["year", "month"])["ran"]
        .agg(run_days="sum", total_days="count")
        .reset_index()
    )
    summary["run_rest_ratio"] = summary["run_days"] / summary["total_days"]
    pivot = summary.pivot(index="year", columns="month", values="run_rest_ratio")

    # Define color map:
    #   0–0.25 (undertraining): yellow
    #   0.25–0.9 (balanced): green
    #   0.9–1.0 (overtraining): red
    cmap = ListedColormap(["#FFD700", "#32CD32", "#FF6347"])  # yellow, green, tomato
    bounds = [0, 0.25, 0.9, 1.0]
    norm = BoundaryNorm(bounds, cmap.N)

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        pivot,
        annot=pivot.notna(),
        fmt=".2f",
        cmap=cmap,
        norm=norm,
        cbar_kws={"label": "Run:Rest Ratio"},
        mask=pivot.isna(),
        linewidths=0.5,
        linecolor="white",
    )
    plt.title("Run:Rest Ratio per Month")
    plt.xlabel("Month")
    plt.ylabel("Year")
    plt.xticks(ticks=np.arange(12) + 0.5, labels=calendar.month_abbr[1:13], rotation=45)
    utils.save_and_close_plot(output_path)


def plot_heatmap_activities(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap of Activities by Day and Hour:
    - x-axis: hour of day (0–23)
    - y-axis: day of week
    - cell = count of runs
    """
    if activities_df.empty:
        return

    activity_data = activities_df.copy()
    dt_col = pd.to_datetime(activity_data["start_date_local"])
    activity_data["weekday"] = dt_col.dt.weekday
    activity_data["hour"] = dt_col.dt.hour

    pivot = activity_data.groupby(["weekday", "hour"]).size().unstack(fill_value=0)

    plt.figure()
    sns.heatmap(pivot, cmap="YlGnBu", cbar_kws={"label": "Count of Runs"})
    plt.title("Heatmap of Activities by Day and Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Day of Week")

    # Adjust ytick labels
    ylabels = [calendar.day_name[i] for i in pivot.index]
    plt.yticks(ticks=np.arange(0.5, 7.5, 1), labels=ylabels, rotation=0)

    utils.save_and_close_plot(output_path)
