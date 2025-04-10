"""
Contains the chart functions, each saving a PNG file.
"""

import calendar
import datetime

import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation.utils import configure_matplotlib_styles

configure_matplotlib_styles()


def _prepare_pace_distance_data(splits_df: pd.DataFrame) -> pd.DataFrame:
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


def _prepare_time_distance_data(activities_df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and augments data for time over distance plot."""
    data = activities_df.copy()
    data["distance_km"] = data["distance_m"] / 1000.0
    data = data[data["distance_km"] >= 0.5]
    data["time_seconds"] = data["moving_time_s"]
    data["year"] = pd.to_datetime(data["start_date_local"]).dt.year
    last_run_date = pd.to_datetime(data["start_date_local"]).max()
    data["is_last_run"] = pd.to_datetime(data["start_date_local"]) == last_run_date
    return data


def _calculate_decay_point(data: pd.DataFrame) -> tuple[float, float]:
    """Calculates decay distance and time for overall trend extension."""
    max_distance = data["distance_km"].max()
    max_time = data["time_seconds"].max()
    decay_distance = max_distance + 2
    average_pace = max_time / max_distance
    decay_time = decay_distance * (average_pace + 180)
    return decay_distance, decay_time


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

    # Format function for y-axis (mm:ss)
    def format_pace(value, _):
        minutes = int(value // 60)
        seconds = int(value % 60)
        return f"{minutes}:{seconds:02d}"

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

    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_pace))
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

    data = _prepare_time_distance_data(activities_df)
    if data.empty:
        return

    decay_distance, decay_time = _calculate_decay_point(data)

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

    def format_minutes_seconds(value, _):
        if np.isnan(value):
            return ""
        minutes = int(value) // 60
        seconds = int(value) % 60
        return f"{minutes}:{seconds:02d}"

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
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_minutes_seconds))
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

    data = _prepare_pace_distance_data(splits_df)
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
    axis.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda val, _: f"{int(val // 60):02d}:{int(val % 60):02d}")
    )
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

    def format_pace(value, _):
        minutes = int(value // 60)
        seconds = int(value % 60)
        return f"{minutes}:{seconds:02d}"

    plt.figure()
    for year in sorted(plot_df["year"].unique()):
        year_data = plot_df[plot_df["year"] == year].sort_values("month")
        plt.plot(year_data["month"], year_data["pace_sec_km"], marker="o", label=str(year))

    plt.title("Fastest 1 km Pace Over Time")
    plt.xlabel("Month")
    plt.ylabel("Fastest Pace (mm:ss)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_pace))
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

    # Format function for y-axis (mm:ss)
    def format_pace(value, _):
        minutes = int(value // 60)
        seconds = int(value % 60)
        return f"{minutes}:{seconds:02d}"

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
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_pace))
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

    # Format function for y-axis (mm:ss)
    def format_pace(value, _):
        minutes = int(value // 60)
        seconds = int(value % 60)
        return f"{minutes}:{seconds:02d}"

    plt.figure()
    axis = sns.boxplot(data=split_data, x="day_of_week", y="pace_sec_km", order=ordered_days)
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_pace))

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
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        rotation=45,
    )
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
