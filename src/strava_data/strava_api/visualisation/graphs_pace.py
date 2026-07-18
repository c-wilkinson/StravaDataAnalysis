"""
Contains the pace chart functions, each saving a PNG file.
"""

# pylint: disable=duplicate-code

import calendar
import matplotlib.dates as mdates
from matplotlib import ticker
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

from strava_data.strava_api.processing.analytics import (
    monthly_pace,
    pace_over_time,
    pace_variability,
)
from strava_data.strava_api.visualisation import interactive_utils, utils


def plot_pace_vs_elevation_change(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plot Running Pace vs. Elevation Change for 1km splits.
    - y-axis: pace (mm:ss)
    - x-axis: elevation change (m)
    - Points coloured by year
    - Trend line included
    """
    splits = utils.prepare_dated_activities(splits_df)
    splits = splits[
        (splits["elevation_difference_m"] >= -100) & (splits["elevation_difference_m"] <= 100)
    ]
    splits["pace_s_km"] = splits["elapsed_time_s"] / (splits["distance_m"] / 1000)
    splits["year"] = pd.to_datetime(splits["start_date_local"]).dt.year

    def plot_fn(axis):
        sns.scatterplot(
            data=splits,
            x="elevation_difference_m",
            y="pace_s_km",
            hue="year",
            alpha=0.6,
            palette="viridis",
            ax=axis,
        )
        sns.regplot(
            data=splits,
            x="elevation_difference_m",
            y="pace_s_km",
            scatter=False,
            color="black",
            line_kws={"linestyle": "--"},
            ci=95,
            ax=axis,
        )
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Running Pace vs. Elevation Change",
        xlabel="Elevation Change (m)",
        ylabel="Split Pace (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_running_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Running pace over time:
    - y-axis: 1 km pace (mm:ss)
    - x-axis: date
    - Points for each ~1 km split
    - Trend line to show changes
    """
    data = utils.prepare_dated_activities(splits_df)
    if data.empty:
        return

    data["pace_sec_km"] = data["elapsed_time_s"] / data["distance_km"]
    data["datetime_obj"] = pd.to_datetime(data["start_date_local"], errors="coerce")
    data["date_numeric"] = mdates.date2num(data["datetime_obj"])
    data.sort_values("date_numeric", inplace=True)

    def plot_fn(axis):
        sns.scatterplot(data=data, x="date_numeric", y="pace_sec_km", alpha=0.5, ax=axis)
        sns.regplot(
            data=data,
            x="date_numeric",
            y="pace_sec_km",
            scatter=False,
            ci=95,
            color="black",
            line_kws={"linestyle": "--"},
            ax=axis,
        )
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axis.set_xticks(data["date_numeric"][:: len(data) // 10 if len(data) >= 10 else 1])
        axis.set_xticklabels(
            [
                d.strftime("%Y-%m")
                for d in data["datetime_obj"].iloc[:: len(data) // 10 if len(data) >= 10 else 1]
            ],
            rotation=45,
        )

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Running Pace Over Time",
        xlabel="Date",
        ylabel="Pace (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_fastest_1km_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the fastest 1km pace per month across all years.
    """
    split_data = utils.prepare_dated_activities(splits_df)
    if split_data.empty:
        return

    split_data["pace_sec_km"] = split_data["elapsed_time_s"] / split_data["distance_km"]
    split_data["year"] = pd.to_datetime(split_data["start_date_local"]).dt.year
    split_data["month"] = pd.to_datetime(split_data["start_date_local"]).dt.month

    monthly_fastest = split_data.groupby(["year", "month"])["pace_sec_km"].min().reset_index()

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

    def plot_fn(axis):
        for year in sorted(plot_df["year"].unique()):
            year_data = plot_df[plot_df["year"] == year].sort_values("month")
            axis.plot(year_data["month"], year_data["pace_sec_km"], marker="o", label=str(year))
        utils.label_month_axis(axis)
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Fastest 1 km Pace Over Time",
        xlabel="Month",
        ylabel="Fastest Pace (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_median_1km_pace_over_time(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the median 1km pace per month across all years.
    """
    split_data = utils.prepare_dated_activities(splits_df)
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

    def plot_fn(axis):
        for year in sorted(plot_df["year"].unique()):
            year_data = plot_df[plot_df["year"] == year].sort_values("month")
            axis.plot(
                year_data["month"],
                year_data["pace_sec_km"],
                marker="o",
                linestyle="-",
                label=str(year),
            )
        utils.label_month_axis(axis)
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Median 1 km Pace Over Time",
        xlabel="Month",
        ylabel="Median Pace (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_pace_by_day_of_week(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Pace by Day of Week:
    - y-axis: 1 km pace (mm:ss), x-axis: day of week
    - Box plot filtered for ~1 km splits
    """
    split_data = utils.prepare_dated_activities(splits_df)
    if split_data.empty:
        return

    split_data["pace_sec_km"] = split_data["elapsed_time_s"] / split_data["distance_km"]
    split_data["day_of_week"] = pd.to_datetime(split_data["start_date_local"]).dt.day_name()
    ordered_days = list(calendar.day_name)

    def plot_fn(axis):
        sns.boxplot(data=split_data, x="day_of_week", y="pace_sec_km", order=ordered_days, ax=axis)
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Pace by Day of Week",
        xlabel="Day of Week",
        ylabel="Pace (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_pace_variability_per_run(splits_df: pd.DataFrame, output_path: str) -> None:
    """
    Plots the standard deviation of pace (in sec/km) for each run over time.
    Only includes activities with at least 3 ~1 km splits.
    """
    splits = utils.prepare_dated_activities(splits_df)
    if splits.empty:
        return

    splits["pace_sec_km"] = splits["elapsed_time_s"] / splits["distance_km"]
    splits.replace([np.inf, -np.inf], np.nan, inplace=True)
    splits.dropna(subset=["pace_sec_km"], inplace=True)

    grouped = (
        splits.groupby(["activity_id", "start_date_local"])
        .agg(pace_std=("pace_sec_km", "std"), split_count=("pace_sec_km", "count"))
        .reset_index()
    )

    grouped = grouped[grouped["split_count"] >= 3]
    grouped["date"] = pd.to_datetime(grouped["start_date_local"])

    if grouped.empty:
        return

    def plot_fn(axis):
        sns.lineplot(data=grouped.sort_values("date"), x="date", y="pace_std", marker="o", ax=axis)
        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.format_pace))
        for label in axis.get_xticklabels():
            label.set_rotation(45)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Pace Variability per Run (Standard Deviation)",
        xlabel="Date",
        ylabel="Pace Std Dev (mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def build_running_pace_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive version of running pace over time."""
    data = pace_over_time(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.scatter(
        data,
        x="activity_date",
        y="pace_sec_km",
        color=data["year"].astype(str),
        labels={"activity_date": "Date", "pace_sec_km": "Pace", "color": "Year"},
        hover_data={
            "activity_id": True,
            "split_index": True,
            "activity_date": "|%d %B %Y",
            "pace_sec_km": ":.0f",
        },
    )
    interactive_utils.add_linear_trend(figure, data["activity_date"], data["pace_sec_km"])
    interactive_utils.apply_layout(figure, "Running pace over time")
    return interactive_utils.apply_pace_axis(figure, data["pace_sec_km"])


def build_fastest_1km_pace_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive fastest one-kilometre pace chart."""
    data = monthly_pace(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="month_start",
        y="fastest_pace_sec_km",
        markers=True,
        labels={"month_start": "Month", "fastest_pace_sec_km": "Pace"},
        hover_data={"month_start": "|%B %Y", "fastest_pace_sec_km": ":.0f"},
    )
    interactive_utils.apply_layout(figure, "Fastest 1 km pace over time")
    return interactive_utils.apply_pace_axis(figure, data["fastest_pace_sec_km"])


def build_median_1km_pace_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive median one-kilometre pace chart."""
    data = monthly_pace(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="month_start",
        y="median_pace_sec_km",
        markers=True,
        labels={"month_start": "Month", "median_pace_sec_km": "Pace"},
        hover_data={"month_start": "|%B %Y", "median_pace_sec_km": ":.0f"},
    )
    interactive_utils.apply_layout(figure, "Median 1 km pace over time")
    return interactive_utils.apply_pace_axis(figure, data["median_pace_sec_km"])


def build_pace_vs_elevation_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive pace-versus-elevation-change chart."""
    data = pace_over_time(splits_df)
    if data.empty:
        return go.Figure()
    data = data[data["elevation_difference_m"].between(-100, 100)]
    figure = px.scatter(
        data,
        x="elevation_difference_m",
        y="pace_sec_km",
        color=data["year"].astype(str),
        labels={
            "elevation_difference_m": "Elevation change (m)",
            "pace_sec_km": "Pace",
            "color": "Year",
        },
        hover_data={"activity_date": "|%d %B %Y", "activity_id": True, "split_index": True},
    )
    interactive_utils.add_linear_trend(figure, data["elevation_difference_m"], data["pace_sec_km"])
    interactive_utils.apply_layout(figure, "Running pace vs elevation change")
    return interactive_utils.apply_pace_axis(figure, data["pace_sec_km"])


def build_pace_by_day_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive pace-by-day-of-week chart."""
    data = pace_over_time(splits_df)
    if data.empty:
        return go.Figure()
    weekday_order = list(calendar.day_name)
    data["weekday"] = pd.Categorical(data["weekday"], categories=weekday_order, ordered=True)
    figure = px.box(
        data,
        x="weekday",
        y="pace_sec_km",
        points="outliers",
        category_orders={"weekday": weekday_order},
        labels={"weekday": "Day", "pace_sec_km": "Pace"},
    )
    figure.update_xaxes(categoryorder="array", categoryarray=weekday_order)
    interactive_utils.apply_layout(figure, "Pace by day of week")
    return interactive_utils.apply_pace_axis(figure, data["pace_sec_km"])


def build_pace_variability_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive pace consistency chart."""
    data = pace_variability(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="activity_date",
        y="pace_std_sec_km",
        markers=True,
        labels={"activity_date": "Date", "pace_std_sec_km": "Pace variation"},
        hover_data={"activity_id": True, "split_count": True, "activity_date": "|%d %B %Y"},
    )
    interactive_utils.apply_layout(figure, "Pace consistency by run")
    return interactive_utils.apply_pace_axis(
        figure, data["pace_std_sec_km"], "Standard deviation (min/km)"
    )
