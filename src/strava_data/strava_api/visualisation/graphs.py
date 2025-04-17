"""
Contains the chart functions, each saving a PNG file.
"""

import calendar
import datetime

import matplotlib.dates as mdates
from matplotlib import ticker
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation import utils

utils.configure_matplotlib_styles()


def plot_pace_vs_elevation_change(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plot Running Pace vs. Elevation Change for 1km splits.
    - y-axis: pace (mm:ss)
    - x-axis: elevation change (m)
    - Points coloured by year
    - Trend line included
    """
    if splits_df.empty:
        return

    # Filter to only ~1 km splits (between 950 and 1050 meters)
    splits = splits_df[(splits_df["distance_m"] > 950) & (splits_df["distance_m"] < 1050)].copy()
    if splits.empty:
        return

    # Remove extreme elevation changes
    splits = splits[
        (splits["elevation_difference_m"] >= -100) & (splits["elevation_difference_m"] <= 100)
    ]

    # Calculate pace in sec/km
    splits["pace_s_km"] = splits["elapsed_time_s"] / (splits["distance_m"] / 1000)

    # Extract year
    splits["year"] = pd.to_datetime(splits["start_date_local"]).dt.year

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=splits,
        x="elevation_difference_m",
        y="pace_s_km",
        hue="year",
        alpha=0.6,
        palette="viridis",
    )

    sns.regplot(
        data=splits,
        x="elevation_difference_m",
        y="pace_s_km",
        scatter=False,
        color="black",
        line_kws={"linestyle": "--"},
        ci=95,
    )

    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    plt.ylabel("Split Pace (mm:ss)")
    plt.xlabel("Elevation Change (m)")
    plt.title("Running Pace vs. Elevation Change")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_time_taken_over_distances(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Time Taken Over Distances:
    - y-axis: total time (hh:mm:ss) with 15-minute intervals
    - x-axis: total distance (km) with 5 km intervals
    - Points colored by year
    - Trend line per year (same color, not labeled)
    - Overall trend in dashed black, labeled
    - Last run marked with a red X
    - Filters out runs shorter than 0.5 km
    - Decay logic: +180s/km added at max distance + 2km
    """
    if activities_df.empty:
        return

    data = utils.prepare_time_distance_data(activities_df)
    if data.empty:
        return

    decay_distance, decay_time = utils.calculate_decay_point(data)

    plt.figure()
    axis = plt.gca()
    palette = sns.color_palette(n_colors=data["year"].nunique())
    year_color_map = dict(zip(sorted(data["year"].unique()), palette))

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year]
        sns.scatterplot(
            data=year_data,
            x="distance_km",
            y="time_seconds",
            color=year_color_map[year],
            alpha=0.5,
            label=year,
            ax=axis,
        )

    last_run = data[data["is_last_run"]]
    if not last_run.empty:
        axis.plot(
            last_run["distance_km"],
            last_run["time_seconds"],
            "x",
            color="red",
            markersize=10,
            label="Last Run",
        )

    for year in sorted(data["year"].unique()):
        sub = data[data["year"] == year][["distance_km", "time_seconds"]].copy()
        sub = pd.concat([pd.DataFrame.from_records([{"distance_km": 0, "time_seconds": 0}]), sub])
        sns.regplot(
            data=sub,
            x="distance_km",
            y="time_seconds",
            scatter=False,
            ci=None,
            truncate=False,
            line_kws={"color": year_color_map[year], "alpha": 0.6},
            ax=axis,
        )

    overall = pd.concat(
        [
            pd.DataFrame.from_records([{"distance_km": 0, "time_seconds": 0}]),
            data[["distance_km", "time_seconds"]],
            pd.DataFrame.from_records(
                [{"distance_km": decay_distance, "time_seconds": decay_time}]
            ),
        ]
    )
    sns.regplot(
        data=overall,
        x="distance_km",
        y="time_seconds",
        scatter=False,
        ci=None,
        color="black",
        line_kws={"linestyle": "--"},
        ax=axis,
        label="Overall Trend",
        truncate=False,
    )

    def seconds_to_hms(value, _):
        return str(datetime.timedelta(seconds=int(value)))

    axis.yaxis.set_major_formatter(ticker.FuncFormatter(seconds_to_hms))
    axis.yaxis.set_major_locator(ticker.MultipleLocator(15 * 60))
    axis.xaxis.set_major_locator(ticker.MultipleLocator(5))

    axis.set_xlim(0, (int(decay_distance / 5) + 1) * 5)
    axis.set_ylim(0, (int((decay_time * 1.05) / (15 * 60)) + 1) * (15 * 60))

    plt.title("Time Taken Over Distances")
    plt.xlabel("Distance (km)")
    plt.ylabel("Time Taken (hh:mm:ss)")
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_running_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Running pace over time:
    - y-axis: 1 km pace (mm:ss)
    - x-axis: date
    - Points for each ~1 km split
    - Trend line to show changes
    """
    if splits_df.empty:
        return

    pace_data = splits_df.copy()
    pace_data["distance_km"] = pace_data["distance_m"] / 1000.0

    # Filter to ~1 km splits (0.95 to 1.05 km)
    pace_data = pace_data[(pace_data["distance_km"] >= 0.95) & (pace_data["distance_km"] <= 1.05)]
    if pace_data.empty:
        return

    pace_data["pace_sec_km"] = pace_data["elapsed_time_s"] / pace_data["distance_km"]
    pace_data["datetime_obj"] = pd.to_datetime(pace_data["start_date_local"], errors="coerce")
    pace_data["date_numeric"] = mdates.date2num(pace_data["datetime_obj"])
    pace_data.sort_values("date_numeric", inplace=True)

    plt.figure()
    axis = plt.gca()
    sns.scatterplot(data=pace_data, x="date_numeric", y="pace_sec_km", alpha=0.5)
    sns.regplot(
        data=pace_data,
        x="date_numeric",
        y="pace_sec_km",
        scatter=False,
        ci=95,
        color="black",
        line_kws={"linestyle": "--"},
    )

    axis.set_title("Running Pace Over Time")
    axis.set_xlabel("Date")
    axis.set_ylabel("Pace (mm:ss)")
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_pace_vs_total_distance(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Running pace vs total distance of that run:
    - x-axis: total distance (km)
    - y-axis: average pace (mm:ss per km)
    - Points colored by year
    - Trend lines by year (matched color, not shown in legend)
    """
    if splits_df.empty:
        return

    data = utils.prepare_pace_distance_data(splits_df)
    if data.empty:
        return

    max_distance = data["distance_km"].max()
    plt.figure()
    axis = plt.gca()

    palette = sns.color_palette(n_colors=data["year"].nunique())
    year_color_map = dict(zip(sorted(data["year"].unique()), palette))

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year]
        sns.scatterplot(
            data=year_data,
            x="distance_km",
            y="pace_sec",
            color=year_color_map[year],
            alpha=0.5,
            label=year,
            ax=axis,
        )

    for year in sorted(data["year"].unique()):
        year_data = data[data["year"] == year].copy()
        if year_data.empty:
            continue
        distance_max = year_data["distance_km"].max()
        pace_max = year_data["pace_sec"].max()
        decay_distance = distance_max + 2
        decay_pace = pace_max + 180

        extended_data = pd.concat(
            [
                year_data,
                pd.DataFrame.from_records(
                    [{"distance_km": decay_distance, "pace_sec": decay_pace}]
                ),
            ]
        )
        sns.regplot(
            data=extended_data,
            x="distance_km",
            y="pace_sec",
            scatter=False,
            ci=None,
            truncate=False,
            line_kws={"color": year_color_map[year], "alpha": 0.6},
            ax=axis,
        )

    plt.xlim(0, max_distance + 3)
    plt.title("Running Pace vs. Total Distance")
    plt.xlabel("Total Distance (km)")
    plt.ylabel("Average Pace (mm:ss per km)")
    axis.yaxis.set_major_formatter(plt.FuncFormatter(utils.format_pace))
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_number_of_runs_per_distance(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Number of runs per distance:
    - Bar graph showing grouped distances (<5 km, 5–10 km, etc.)
    - Bars per year + an overall bar
    """
    if activities_df.empty:
        return

    distance_data = activities_df.copy()
    distance_data["distance_km"] = distance_data["distance_m"] / 1000.0
    distance_data["year"] = pd.to_datetime(distance_data["start_date_local"]).dt.year

    # Define bins for distance categories
    bins = [0, 5, 10, 15, 20, 25, 30, 9999]
    labels = ["<5", "5–10", "10–15", "15–20", "20–25", "25–30", "30+"]
    distance_data["distance_bin"] = pd.cut(
        distance_data["distance_km"], bins=bins, labels=labels, include_lowest=True
    )

    # Count runs per bin and year
    grouped = distance_data.groupby(["distance_bin", "year"]).size().reset_index(name="count")

    plt.figure()
    sns.barplot(data=grouped, x="distance_bin", y="count", hue="year", errorbar=None)
    plt.title("Number of Runs per Distance")
    plt.xlabel("Distance Range (km)")
    plt.ylabel("Count of Runs")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_fastest_1km_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the fastest 1km pace per month across all years.
    """
    if splits_df.empty:
        return

    split_data = splits_df.copy()
    split_data["distance_km"] = split_data["distance_m"] / 1000.0

    # Filter ~1 km splits
    split_data = split_data[
        (split_data["distance_km"] >= 0.95) & (split_data["distance_km"] <= 1.05)
    ]
    if split_data.empty:
        return

    split_data["pace_sec_km"] = split_data["elapsed_time_s"] / split_data["distance_km"]
    split_data["year"] = pd.to_datetime(split_data["start_date_local"]).dt.year
    split_data["month"] = pd.to_datetime(split_data["start_date_local"]).dt.month

    monthly_fastest = split_data.groupby(["year", "month"])["pace_sec_km"].min().reset_index()

    # Fill in missing months
    all_years = sorted(monthly_fastest["year"].unique())
    rows = []
    for year in all_years:
        for month in range(1, 13):
            pace = monthly_fastest.loc[
                (monthly_fastest["year"] == year) & (monthly_fastest["month"] == month),
                "pace_sec_km",
            ]
            pace_val = pace.values[0] if not pace.empty else np.nan
            rows.append({"year": year, "month": month, "pace_sec_km": pace_val})

    plot_df = pd.DataFrame(rows)
    plot_df["pace_sec_km"] = plot_df.groupby("year")["pace_sec_km"].ffill()

    plt.figure()
    for year in sorted(plot_df["year"].unique()):
        year_data = plot_df[plot_df["year"] == year].sort_values("month")
        plt.plot(year_data["month"], year_data["pace_sec_km"], marker="o", label=str(year))

    plt.title("Fastest 1 km Pace Over Time")
    plt.xlabel("Month")
    plt.ylabel("Fastest Pace (mm:ss)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_median_1km_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the median 1km pace per month across all years.
    """
    if splits_df.empty:
        return

    split_data = splits_df.copy()
    split_data["distance_km"] = split_data["distance_m"] / 1000.0

    # Filter ~1 km splits
    split_data = split_data[
        (split_data["distance_km"] >= 0.95) & (split_data["distance_km"] <= 1.05)
    ]
    if split_data.empty:
        return

    split_data["pace_sec_km"] = split_data["elapsed_time_s"] / split_data["distance_km"]
    split_data["year"] = pd.to_datetime(split_data["start_date_local"]).dt.year
    split_data["month"] = pd.to_datetime(split_data["start_date_local"]).dt.month

    monthly_medians = split_data.groupby(["year", "month"])["pace_sec_km"].median().reset_index()

    all_years = monthly_medians["year"].unique()
    rows = []
    for year in all_years:
        for month in range(1, 13):
            val = monthly_medians.loc[
                (monthly_medians["year"] == year) & (monthly_medians["month"] == month),
                "pace_sec_km",
            ]
            pace_val = val.values[0] if not val.empty else np.nan
            rows.append({"year": year, "month": month, "pace_sec_km": pace_val})

    plot_df = pd.DataFrame(rows)
    plot_df["pace_sec_km"] = plot_df.groupby("year")["pace_sec_km"].ffill()

    plt.figure()
    for year in sorted(plot_df["year"].unique()):
        year_data = plot_df[plot_df["year"] == year].sort_values("month")
        plt.plot(
            year_data["month"], year_data["pace_sec_km"], marker="o", linestyle="-", label=str(year)
        )

    plt.title("Median 1 km Pace Over Time")
    plt.xlabel("Month")
    plt.ylabel("Median Pace (mm:ss)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_total_distance_by_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Total distance run by month:
    - x-axis: months (Jan–Dec)
    - y-axis: total distance run (km)
    - Separate line graph for each year
    """
    if activities_df.empty:
        return

    activity_data = activities_df.copy()
    activity_data["distance_km"] = activity_data["distance_m"] / 1000.0
    activity_data["year"] = pd.to_datetime(activity_data["start_date_local"]).dt.year
    activity_data["month"] = pd.to_datetime(activity_data["start_date_local"]).dt.month

    monthly_totals = activity_data.groupby(["year", "month"])["distance_km"].sum().reset_index()

    plt.figure()
    for year in sorted(monthly_totals["year"].unique()):
        year_data = monthly_totals[monthly_totals["year"] == year].sort_values("month")
        plt.plot(
            year_data["month"], year_data["distance_km"], marker="o", linestyle="-", label=str(year)
        )

    plt.title("Total Distance Run by Month")
    plt.xlabel("Month")
    plt.ylabel("Total Distance (km)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_pace_by_day_of_week(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Pace by Day of Week:
    - y-axis: 1 km pace (mm:ss), x-axis: day of week
    - Box plot filtered for ~1 km splits
    """
    if splits_df.empty:
        return

    split_data = splits_df.copy()
    split_data["distance_km"] = split_data["distance_m"] / 1000.0

    # Filter to ~1 km splits (0.95 to 1.05 km)
    split_data = split_data[
        (split_data["distance_km"] >= 0.95) & (split_data["distance_km"] <= 1.05)
    ]
    if split_data.empty:
        return

    split_data["pace_sec_km"] = split_data["elapsed_time_s"] / split_data["distance_km"]
    split_data["day_of_week"] = pd.to_datetime(split_data["start_date_local"]).dt.day_name()

    ordered_days = list(calendar.day_name)

    plt.figure()
    axis = sns.boxplot(data=split_data, x="day_of_week", y="pace_sec_km", order=ordered_days)
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))

    plt.title("Pace by Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Pace (mm:ss)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_cumulative_distance_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Cumulative distance per month:
    - x-axis: ['Jan', 'Feb', ..., 'Dec']
    - y-axis: cumulative distance (km)
    - Separate line per year
    """
    if activities_df.empty:
        return

    activity_data = activities_df.copy()
    activity_data["distance_km"] = activity_data["distance_m"] / 1000.0
    activity_data["year"] = pd.to_datetime(activity_data["start_date_local"]).dt.year
    activity_data["month"] = pd.to_datetime(activity_data["start_date_local"]).dt.month

    # Monthly aggregation
    monthly_df = activity_data.groupby(["year", "month"])["distance_km"].sum().reset_index()

    # Prepare data for plotting with cumulative sums
    plt.figure()
    for year in sorted(monthly_df["year"].unique()):
        sub = monthly_df[monthly_df["year"] == year].copy()
        sub = sub.set_index("month").reindex(range(1, 13), fill_value=0).reset_index()
        sub["cum_dist"] = sub["distance_km"].cumsum()
        plt.plot(sub["month"], sub["cum_dist"], marker="o", label=str(year))

    plt.title("Cumulative Distance per Year")
    plt.xlabel("Month")
    plt.ylabel("Cumulative Distance (km)")
    plt.xticks(
        range(1, 13),
        calendar.month_abbr[1:13],
        rotation=45,
    )
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_longest_run_per_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Scatter plot of longest run per month across all years.
    - X-axis: month (Jan–Dec)
    - Y-axis: longest run (km)
    - Points: one per year-month, only if a run occurred
    - Colour-coded by year
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    longest_per_month = data.groupby(["year", "month"])["distance_km"].max().reset_index()

    plt.figure()
    for year in sorted(longest_per_month["year"].unique()):
        year_data = longest_per_month[longest_per_month["year"] == year]
        plt.scatter(
            year_data["month"],
            year_data["distance_km"],
            label=str(year),
            alpha=0.7,
            s=60,
        )

    plt.title("Longest Run per Month")
    plt.xlabel("Month")
    plt.ylabel("Distance (km)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13])
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_monthly_distance_by_year_grouped(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Clustered bar chart comparing total monthly distance by year.
    - X-axis: Month (Jan–Dec)
    - Y-axis: Total distance (km)
    - Grouped by year
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    data["month"] = pd.to_datetime(data["start_date_local"]).dt.month

    grouped = data.groupby(["month", "year"])["distance_km"].sum().reset_index()

    # Pivot for seaborn's barplot
    pivot = grouped.pivot(index="month", columns="year", values="distance_km")
    pivot = pivot.fillna(0)

    pivot = pivot.sort_index()  # Ensure months are ordered 1-12
    month_labels = [calendar.month_abbr[m] for m in pivot.index]

    plt.figure(figsize=(12, 6))
    pivot.plot(kind="bar", width=0.8)
    plt.xticks(ticks=range(len(month_labels)), labels=month_labels, rotation=45)
    plt.ylabel("Total Distance (km)")
    plt.xlabel("Month")
    plt.title("Year-over-Year Monthly Distance Comparison")
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_rolling_distance(activities_df: pd.DataFrame, output_path: str, window: int = 30) -> None:
    """
    Line graph showing rolling X-day distance total.
    Default window = 30 days.
    """
    if activities_df.empty:
        return

    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data["start_date"] = pd.to_datetime(data["start_date_local"])

    # Sort by date
    data = data.sort_values("start_date")

    # Group by day and sum distances (in case of multiple runs per day)
    daily = data.groupby("start_date")["distance_km"].sum().reset_index()

    # Calculate rolling total
    daily["rolling_distance_km"] = daily["distance_km"].rolling(window=window).sum()

    plt.figure()
    plt.plot(daily["start_date"], daily["rolling_distance_km"], color="blue", linewidth=2)
    plt.title(f"Rolling {window}-Day Distance")
    plt.xlabel("Date")
    plt.ylabel("Distance (km)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_pace_variability_per_run(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the standard deviation of pace (in sec/km) for each run over time.
    Only includes activities with at least 3 ~1 km splits.
    """
    if splits_df.empty:
        return

    splits = splits_df.copy()
    splits["distance_km"] = splits["distance_m"] / 1000
    splits = splits[(splits["distance_km"] >= 0.95) & (splits["distance_km"] <= 1.05)]
    if splits.empty:
        return

    splits["pace_sec_km"] = splits["elapsed_time_s"] / splits["distance_km"]

    grouped = (
        splits.groupby(["activity_id", "start_date_local"])
        .agg(pace_std=("pace_sec_km", "std"), split_count=("pace_sec_km", "count"))
        .reset_index()
    )

    # Filter to runs with at least 3 splits
    grouped = grouped[grouped["split_count"] >= 3]
    grouped["date"] = pd.to_datetime(grouped["start_date_local"])

    if grouped.empty:
        return

    plt.figure()
    axis = plt.gca()
    sns.lineplot(data=grouped.sort_values("date"), x="date", y="pace_std", marker="o", ax=axis)

    axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
    axis.set_title("Pace Variability per Run (Standard Deviation)")
    axis.set_xlabel("Date")
    axis.set_ylabel("Pace Std Dev (mm:ss)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
