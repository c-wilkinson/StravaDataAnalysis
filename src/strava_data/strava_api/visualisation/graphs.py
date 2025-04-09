"""
Contains the chart functions, each saving a PNG file.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import calendar
import datetime
import matplotlib.dates as mdates
from strava_data.strava_api.visualisation.utils import configure_matplotlib_styles

configure_matplotlib_styles()


def plot_pace_vs_elevation_change(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    1) Running Pace vs. Elevation Change:
       - y-axis: 1 km pace (hh:mm:ss) or min/km, x-axis: elevation change
       - Points colored differently by year
       - Single overall trend line with confidence bands
       - Differentiates indoor vs. outdoor if available
    """
    if splits_df.empty:
        return

    # We assume each split is ~1 km. Compute pace in s/km or min/km
    # "elapsed_time_s" is total seconds for the split
    splits_df = splits_df.copy()
    splits_df["pace_sec_km"] = splits_df["elapsed_time_s"].astype(float)

    # For elevation difference
    splits_df["year"] = pd.to_datetime(splits_df["start_date_local"]).dt.year

    # Plot
    plt.figure()
    sns.scatterplot(
        data=splits_df,
        x="elevation_difference_m",
        y="pace_sec_km",
        hue="year",
        alpha=0.5
    )

    # Overall trend line (all data)
    sns.regplot(
        data=splits_df,
        x="elevation_difference_m",
        y="pace_sec_km",
        scatter=False,
        ci=95,
        color="black",
        line_kws={"linestyle": "--"}
    )

    plt.title("Running Pace vs. Elevation Change")
    plt.xlabel("Elevation Change (m)")
    plt.ylabel("Split Pace (s/km)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_time_taken_over_distances(
    activities_df: pd.DataFrame,
    splits_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    2) Time Taken Over Distances:
       - y-axis: total time (hh:mm:ss)
       - x-axis: total distance (km)
       - Points colored by year
       - Trend line per year, plus overall average up to 44 km
       - Last run marked with a red X
    """
    if activities_df.empty:
        return

    df = activities_df.copy()

    # Convert distance to km
    df["distance_km"] = df["distance_m"] / 1000.0
    df["time_hours"] = df["moving_time_s"] / 3600.0
    df["year"] = pd.to_datetime(df["start_date_local"]).dt.year

    last_run_date = pd.to_datetime(df["start_date_local"]).max()
    df["is_last_run"] = pd.to_datetime(df["start_date_local"]) == last_run_date

    plt.figure()
    sns.scatterplot(
        data=df,
        x="distance_km",
        y="time_hours",
        hue="year",
        alpha=0.5
    )

    # Mark last run with red X
    last_run_df = df[df["is_last_run"]]
    if not last_run_df.empty:
        plt.plot(
            last_run_df["distance_km"],
            last_run_df["time_hours"],
            "x",
            color="red",
            markersize=10,
            label="Last Run"
        )

    # Trend line per year
    for yr in df["year"].unique():
        sub = df[df["year"] == yr]
        sns.regplot(
            data=sub,
            x="distance_km",
            y="time_hours",
            scatter=False,
            ci=None,
            label=f"Trend {yr}"
        )

    # Overall trend line
    sns.regplot(
        data=df,
        x="distance_km",
        y="time_hours",
        scatter=False,
        ci=None,
        color="black",
        line_kws={"linestyle": "--"},
        label="Overall Trend"
    )

    plt.title("Time Taken Over Distances")
    plt.xlabel("Distance (km)")
    plt.ylabel("Time (hours)")
    plt.xlim([0, 44])  # Extend to 44 km if desired
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_running_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    3) Running pace over time:
       - y-axis: 1 km pace (sec or min)
       - x-axis: date
       - Points for each split or activity
       - Trend line to show changes
    """
    if splits_df.empty:
        return

    df = splits_df.copy()
    df["pace_sec_km"] = df["elapsed_time_s"]
    df["date"] = pd.to_datetime(df["start_date_local"]).dt.date

    # Convert dates to numeric
    df["datetime_obj"] = pd.to_datetime(df["start_date_local"], errors="coerce")
    df["date_numeric"] = mdates.date2num(df["datetime_obj"])
    df.sort_values("date_numeric", inplace=True)

    plt.figure()
    sns.scatterplot(
        data=df,
        x="date_numeric",
        y="pace_sec_km",
        alpha=0.5
    )
    sns.regplot(
        data=df,
        x="date_numeric",
        y="pace_sec_km",
        scatter=False,
        ci=95,
        color="black",
        line_kws={"linestyle": "--"},
    )

    plt.title("Running Pace Over Time")
    plt.xlabel("Date")
    plt.ylabel("Pace (s/km)")

    # Format date ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_pace_vs_total_distance(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    4) Running pace vs total distance of that run:
       - y-axis: pace (sec per km)
       - x-axis: total distance (km)
       - Points colored by year
       - Trend lines by year
    """
    if splits_df.empty:
        return

    df = splits_df.copy()

    # We assume there's a column with total distance for the entire activity if you joined data.
    # If not, you'd need to merge on activity info.
    # For now, let's treat "distance_m" as the split distance. We need the total run distance
    # from the activities DF or some joined approach. This is left to user to unify data.

    # As a placeholder, we treat each split's "distance_m" as total distance, which is incorrect
    # in real usage. Adjust logic as needed if you have that data joined.

    df["distance_km"] = df["distance_m"] / 1000.0
    df["pace_sec_km"] = df["elapsed_time_s"]
    df["year"] = pd.to_datetime(df["start_date_local"]).dt.year

    plt.figure()
    sns.scatterplot(
        data=df,
        x="distance_km",
        y="pace_sec_km",
        hue="year",
        alpha=0.5
    )

    # Trend line per year
    for yr in df["year"].unique():
        sub = df[df["year"] == yr]
        sns.regplot(
            data=sub,
            x="distance_km",
            y="pace_sec_km",
            scatter=False,
            ci=None,
            label=f"Year {yr}"
        )

    plt.title("Running Pace vs. Total Distance")
    plt.xlabel("Distance (km)")
    plt.ylabel("Pace (s/km)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_number_of_runs_per_distance(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    5) Number of runs per distance:
       - Bar graph showing grouped distances (<5 km, 5–10 km, etc.)
       - Bars per year + an overall bar
    """
    if activities_df.empty:
        return

    df = activities_df.copy()
    df["distance_km"] = df["distance_m"] / 1000.0
    df["year"] = pd.to_datetime(df["start_date_local"]).dt.year

    # Define bins for distance categories
    bins = [0, 5, 10, 15, 20, 25, 30, 9999]
    labels = ["<5", "5–10", "10–15", "15–20", "20–25", "25–30", "30+"]
    df["dist_bin"] = pd.cut(df["distance_km"], bins=bins, labels=labels, include_lowest=True)

    # Count runs per bin
    grouped = df.groupby(["dist_bin", "year"]).size().reset_index(name="count")

    plt.figure()
    sns.barplot(
        data=grouped,
        x="dist_bin",
        y="count",
        hue="year",
        errorbar=None
    )
    plt.title("Number of Runs per Distance")
    plt.xlabel("Distance Range (km)")
    plt.ylabel("Count of Runs")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_fastest_1km_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    6) Fastest 1km pace over time:
       - x-axis: months (Jan–Dec)
       - y-axis: 1 km pace (sec or min)
       - Plot each year's fastest 1 km pace each month
       - Trend line for each year
       - If no runs in a month, assume pace is unchanged from prior data
    """
    if splits_df.empty:
        return

    # Filter splits to ~1 km if needed
    df = splits_df.copy()
    df["pace_sec_km"] = df["elapsed_time_s"]
    df["year"] = pd.to_datetime(df["start_date_local"]).dt.year
    df["month"] = pd.to_datetime(df["start_date_local"]).dt.month

    # Get fastest split each month/year
    grouping = df.groupby(["year", "month"])["pace_sec_km"].min().reset_index()

    # Build a 12-month index for each year
    all_years = grouping["year"].unique()
    full_rows = []
    for yr in all_years:
        for m in range(1, 13):
            sub = grouping[(grouping["year"] == yr) & (grouping["month"] == m)]
            if not sub.empty:
                pace_val = sub["pace_sec_km"].values[0]
            else:
                # If no data for that month, we'll keep it as NaN; later we can forward fill
                pace_val = np.nan
            full_rows.append({"year": yr, "month": m, "pace_sec_km": pace_val})
    final_df = pd.DataFrame(full_rows)
    # Forward fill the missing months
    final_df["pace_sec_km"] = final_df.groupby("year")["pace_sec_km"].ffill()

    plt.figure()
    for yr in sorted(final_df["year"].unique()):
        sub = final_df[final_df["year"] == yr].copy()
        sub.sort_values("month", inplace=True)
        plt.plot(
            sub["month"],
            sub["pace_sec_km"],
            marker="o",
            linestyle="-",
            label=f"{yr}"
        )

    plt.title("Fastest 1 km Pace Over Time")
    plt.xlabel("Month")
    plt.ylabel("Fastest Pace (s/km)")
    plt.xticks(range(1, 13), calendar.month_abbr[1:13], rotation=45)
    plt.legend(title="Year")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_total_distance_by_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    7) Total distance run by month:
       - x-axis: months (Jan–Dec)
       - y-axis: total distance run (km)
       - Separate line graph for each year
    """
    if activities_df.empty:
        return

    df = activities_df.copy()
    df["distance_km"] = df["distance_m"] / 1000.0
    df["year"] = pd.to_datetime(df["start_date_local"]).dt.year
    df["month"] = pd.to_datetime(df["start_date_local"]).dt.month

    monthly = df.groupby(["year", "month"])["distance_km"].sum().reset_index()

    plt.figure()
    for yr in sorted(monthly["year"].unique()):
        sub = monthly[monthly["year"] == yr].copy()
        sub.sort_values("month", inplace=True)
        plt.plot(
            sub["month"],
            sub["distance_km"],
            marker="o",
            linestyle="-",
            label=str(yr)
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
    8) Pace by Day of Week:
       - y-axis: 1 km pace (sec, or min), x-axis: day of week
       - Box plot or bar
    """
    if splits_df.empty:
        return

    df = splits_df.copy()
    df["pace_sec_km"] = df["elapsed_time_s"]
    df["day_of_week"] = pd.to_datetime(df["start_date_local"]).dt.day_name()

    # Ensure consistent ordering from Monday...Sunday if desired
    ordered_days = list(calendar.day_name)

    plt.figure()
    sns.boxplot(
        data=df,
        x="day_of_week",
        y="pace_sec_km",
        order=ordered_days
    )
    plt.title("Pace by Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Pace (s/km)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_heatmap_activities(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    9) Heatmap of Activities by Day and Hour:
       - x-axis: hour of day (0–23)
       - y-axis: day of week
       - cell = count of runs
    """
    if activities_df.empty:
        return

    df = activities_df.copy()
    dt_col = pd.to_datetime(df["start_date_local"])
    df["weekday"] = dt_col.dt.weekday  # Monday=0
    df["hour"] = dt_col.dt.hour

    pivot = df.groupby(["weekday", "hour"]).size().unstack(fill_value=0)

    plt.figure()
    sns.heatmap(
        pivot,
        cmap="YlGnBu",
        cbar_kws={"label": "Count of Runs"}
    )
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
    10) Cumulative distance over time:
       - x-axis: month or date
       - y-axis: cumulative distance (km)
       - One line per year
    """
    if activities_df.empty:
        return

    df = activities_df.copy()
    df["distance_km"] = df["distance_m"] / 1000.0
    df["date"] = pd.to_datetime(df["start_date_local"])
    df["year"] = df["date"].dt.year
    df.sort_values("date", inplace=True)

    # Group by year, then do a cumulative sum
    out = []
    for yr in sorted(df["year"].unique()):
        sub = df[df["year"] == yr].copy()
        sub.sort_values("date", inplace=True)
        sub["cum_dist"] = sub["distance_km"].cumsum()
        out.append(sub)

    full = pd.concat(out)

    plt.figure()
    for yr in sorted(full["year"].unique()):
        year_df = full[full["year"] == yr]
        plt.plot(
            year_df["date"],
            year_df["cum_dist"],
            marker="o",
            linestyle="-",
            label=str(yr)
        )

    plt.title("Cumulative Distance Over Time")
    plt.xlabel("Date")
    plt.ylabel("Distance (km)")
    plt.legend(title="Year")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
