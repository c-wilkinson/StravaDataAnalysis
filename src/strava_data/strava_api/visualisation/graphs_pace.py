"""
Contains the pace chart functions, each saving a PNG file.
"""

import calendar

import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from strava_data.strava_api.visualisation import utils


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
    utils.save_and_close_plot(output_path)


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
    utils.save_and_close_plot(output_path)


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
    utils.save_and_close_plot(output_path)


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
    utils.save_and_close_plot(output_path)


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
    utils.save_and_close_plot(output_path)


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
    utils.save_and_close_plot(output_path)
