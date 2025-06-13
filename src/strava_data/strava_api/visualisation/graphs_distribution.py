"""
Contains the distribution chart functions, each saving a PNG file.
"""

import calendar
from matplotlib import ticker
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation import utils


def plot_run_distance_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plot showing distribution of run distances, split by year.
    Highlights distance preferences and training evolution over time.
    """
    data = utils.prepare_dated_activities(activities_df)

    def plot_fn(axis):
        for year in sorted(data["year"].unique()):
            year_data = data[data["year"] == year]
            if year_data["distance_km"].nunique() > 1:
                sns.kdeplot(
                    year_data["distance_km"],
                    fill=True,
                    label=str(year),
                    alpha=0.3,
                    ax=axis,
                )
        axis.set_xlim(left=0)
        axis.legend(title="Year")
        axis.grid(True, linestyle="--", linewidth=0.5)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Run Distance Distribution by Year",
        xlabel="Distance (km)",
        ylabel="Density",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_pace_distribution(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plot showing distribution of paces (in mm:ss per km), one per year.
    Only includes ~1 km splits.
    """
    data = utils.prepare_dated_activities(splits_df)
    if data.empty:
        return

    data["pace_sec_km"] = data["elapsed_time_s"] / data["distance_km"]

    def plot_fn(axis):
        for year in sorted(data["year"].unique()):
            year_data = data[data["year"] == year]
            if year_data["pace_sec_km"].nunique() > 1:
                sns.kdeplot(
                    year_data["pace_sec_km"],
                    fill=True,
                    label=str(year),
                    alpha=0.3,
                    ax=axis,
                )
        axis.xaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
        axis.legend(title="Year")
        axis.grid(True)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Pace Distribution by Year (1 km splits)",
        xlabel="Pace (mm:ss)",
        ylabel="Density",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_elevation_gain_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    KDE plots showing distribution of elevation gain per run, one per year.
    Highlights how hilly your training was year-to-year.
    """
    data = utils.prepare_dated_activities(activities_df)
    data = data[data["total_elevation_gain_m"] != 0]

    def plot_fn(axis):
        for year in sorted(data["year"].unique()):
            year_data = data[data["year"] == year]
            if year_data["total_elevation_gain_m"].nunique() > 1:
                sns.kdeplot(
                    year_data["total_elevation_gain_m"],
                    fill=True,
                    label=str(year),
                    alpha=0.3,
                    ax=axis,
                )
        axis.legend(title="Year")
        axis.grid(True, linestyle="--", linewidth=0.5)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Elevation Gain per Run (by Year)",
        xlabel="Elevation Gain (m)",
        ylabel="Density",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_heart_rate_zone_distribution(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Stacked bar chart showing time spent in heart rate zones per month.
    Only includes ~1 km splits with valid heart rate data.
    """
    data = utils.prepare_dated_activities(splits_df)
    data = data[pd.notnull(data["average_heartrate"])]

    if data.empty:
        return

    data["month_label"] = (
        pd.to_datetime(data["start_date_local"]).dt.tz_localize(None).dt.to_period("M").astype(str)
    )
    data["hr_zone"] = data.apply(
        lambda row: utils.classify_zone_dynamic(row["average_heartrate"], row["start_date_local"]),
        axis=1,
    )
    data["time_min"] = data["elapsed_time_s"] / 60.0
    grouped = data.groupby(["month_label", "hr_zone"])["time_min"].sum().unstack().fillna(0)
    grouped = grouped.sort_index()

    def plot_fn(axis):
        grouped.plot(kind="bar", stacked=True, figsize=(14, 6), colormap="viridis", ax=axis)
        axis.set_xticks(range(len(grouped.index)))
        axis.set_xticklabels([str(label) for label in grouped.index], rotation=45)
        axis.legend(title="Heart Rate Zone")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Training Intensity by Heart Rate Zone",
        xlabel="Month",
        ylabel="Time Spent (minutes)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_run_start_time_distribution(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Box plot showing distribution of run start times by month.
    - X-axis: Month (Jan–Dec)
    - Y-axis: Hour of day (0–23)
    """
    if activities_df.empty:
        return

    data = utils.prepare_activities_with_distance(activities_df)
    data["start_time"] = pd.to_datetime(data["start_date_local"], errors="coerce")
    data["hour"] = data["start_time"].dt.hour

    if data[["month", "hour"]].dropna().empty:
        return

    def plot_fn(axis):
        sns.boxplot(data=data, x="month", y="hour", ax=axis)
        axis.set_xticks(ticks=range(0, 12))
        axis.set_xticklabels(labels=calendar.month_abbr[1:13])

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Distribution of Run Start Time by Month",
        xlabel="Month",
        ylabel="Start Hour of Day",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


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

    run_days = data.drop_duplicates(subset="date")
    summary = run_days.groupby(["year", "month"]).size().reset_index(name="run_day_count")
    pivot = summary.pivot(index="year", columns="month", values="run_day_count")

    def plot_fn(axis):
        sns.heatmap(
            pivot,
            annot=pivot,
            fmt=".0f",
            cmap="Greens",
            cbar_kws={"label": "Run Days"},
            mask=pivot.isna(),
            ax=axis,
        )
        utils.label_month_axis_barplot(axis)
        axis.set_xlabel("Month")
        axis.set_ylabel("Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Run Days per Month",
        xlabel="Month",
        ylabel="Year",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_rest_days_heatmap(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap showing number of rest days per month.
    Only annotates months where rest days occurred.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["date"] = pd.to_datetime(data["start_date_local"]).dt.date

    start = data["date"].min()
    end = data["date"].max()
    full_dates = pd.DataFrame({"date": [d.date() for d in pd.date_range(start, end)]})

    rest_days = full_dates[~full_dates["date"].isin(data["date"])].copy()
    rest_days["year"] = pd.to_datetime(rest_days["date"]).dt.year
    rest_days["month"] = pd.to_datetime(rest_days["date"]).dt.month

    rest_summary = rest_days.groupby(["year", "month"]).size().reset_index(name="rest_day_count")
    pivot = rest_summary.pivot(index="year", columns="month", values="rest_day_count")

    def plot_fn(axis):
        sns.heatmap(
            pivot,
            annot=pivot,
            fmt=".0f",
            cmap="Reds",
            cbar_kws={"label": "Rest Days"},
            mask=pivot.isna(),
            ax=axis,
        )
        utils.label_month_axis_barplot(axis)
        axis.set_xlabel("Month")
        axis.set_ylabel("Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Rest Days per Month",
        xlabel="Month",
        ylabel="Year",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


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

    cmap = ListedColormap(["#FFD700", "#32CD32", "#FF6347"])
    bounds = [0, 0.25, 0.9, 1.0]
    norm = BoundaryNorm(bounds, cmap.N)

    def plot_fn(axis):
        sns.heatmap(
            pivot,
            annot=pivot,
            fmt=".2f",
            cmap=cmap,
            norm=norm,
            cbar_kws={"label": "Run:Rest Ratio"},
            mask=pivot.isna(),
            linewidths=0.5,
            linecolor="white",
            ax=axis,
        )
        utils.label_month_axis_barplot(axis)
        axis.set_xlabel("Month")
        axis.set_ylabel("Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Run:Rest Ratio per Month",
        xlabel="Month",
        ylabel="Year",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


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

    def plot_fn(axis):
        sns.heatmap(pivot, cmap="YlGnBu", cbar_kws={"label": "Count of Runs"}, ax=axis)
        axis.set_xlabel("Hour of Day")
        axis.set_ylabel("Day of Week")
        ylabels = [calendar.day_name[i] for i in pivot.index]
        axis.set_yticks(ticks=np.arange(0.5, 7.5, 1))
        axis.set_yticklabels(labels=ylabels, rotation=0)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Heatmap of Activities by Day and Hour",
        xlabel="Hour of Day",
        ylabel="Day of Week",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801
