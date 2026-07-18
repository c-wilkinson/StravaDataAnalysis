"""
Contains the distance chart functions, each saving a PNG file.
"""

# pylint: disable=duplicate-code

import calendar
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import ticker
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from strava_data.strava_api.processing.analytics import (
    cumulative_distance,
    longest_run_by_month,
    monthly_distance,
    prepare_activities,
    prepare_splits,
    rolling_distance,
)
from strava_data.strava_api.visualisation import interactive_utils, utils


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
    palette = sns.color_palette(n_colors=data["year"].nunique())
    year_color_map = dict(zip(sorted(data["year"].unique()), palette))

    def plot_fn(axis):
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
            sub = pd.concat(
                [pd.DataFrame.from_records([{"distance_km": 0, "time_seconds": 0}]), sub]
            )
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

        axis.yaxis.set_major_formatter(ticker.FuncFormatter(utils.seconds_to_hms))
        axis.yaxis.set_major_locator(ticker.MultipleLocator(15 * 60))
        axis.xaxis.set_major_locator(ticker.MultipleLocator(5))
        axis.set_xlim(0, (int(decay_distance / 5) + 1) * 5)
        axis.set_ylim(0, (int((decay_time * 1.05) / (15 * 60)) + 1) * (15 * 60))
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Time Taken Over Distances",
        xlabel="Distance (km)",
        ylabel="Time Taken (hh:mm:ss)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_time_taken_over_distances_recent_years(
    activities_df: pd.DataFrame,
    output_path: str,
) -> None:
    """
    Time Taken Over Distances (Recent Years Only):
    - Same as plot_time_taken_over_distances but filtered to current and previous year.
    """
    if activities_df.empty:
        return

    activities_df["start_date_local"] = pd.to_datetime(activities_df["start_date_local"])

    current_year = datetime.now().year
    years_to_include = {current_year, current_year - 1}
    filtered_df = activities_df[activities_df["start_date_local"].dt.year.isin(years_to_include)]

    # Reuse original plotting function on filtered data
    plot_time_taken_over_distances(filtered_df, output_path)


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
    palette = sns.color_palette(n_colors=data["year"].nunique())
    year_color_map = dict(zip(sorted(data["year"].unique()), palette))

    def plot_fn(axis):
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

        axis.set_xlim(0, max_distance + 3)
        axis.yaxis.set_major_formatter(plt.FuncFormatter(utils.format_pace))
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Running Pace vs. Total Distance",
        xlabel="Total Distance (km)",
        ylabel="Average Pace (mm:ss per km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_number_of_runs_per_distance(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Number of runs per distance:
    - Bar graph showing grouped distances (<5 km, 5–10 km, etc.)
    - Bars per year + an overall bar
    """
    data = utils.prepare_dated_activities(activities_df)
    data["distance_bin"] = pd.cut(
        data["distance_km"],
        bins=[0, 5, 10, 15, 20, 25, 30, 9999],
        labels=["<5", "5–10", "10–15", "15–20", "20–25", "25–30", "30+"],
        include_lowest=True,
    )

    grouped = data.groupby(["distance_bin", "year"], observed=True).size().reset_index(name="count")

    def plot_fn(axis):
        sns.barplot(data=grouped, x="distance_bin", y="count", hue="year", errorbar=None, ax=axis)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Number of Runs per Distance",
        xlabel="Distance Range (km)",
        ylabel="Count of Runs",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_total_distance_by_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Total distance run by month:
    - x-axis: months (Jan–Dec)
    - y-axis: total distance run (km)
    - Separate line graph for each year
    """
    data = utils.prepare_dated_activities(activities_df)
    monthly_totals = data.groupby(["year", "month"])["distance_km"].sum().reset_index()

    def plot_fn(axis):
        for year in sorted(monthly_totals["year"].unique()):
            year_data = monthly_totals[monthly_totals["year"] == year].sort_values("month")
            axis.plot(
                year_data["month"],
                year_data["distance_km"],
                marker="o",
                linestyle="-",
                label=str(year),
            )
        utils.label_month_axis(axis)
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Total Distance Run by Month",
        xlabel="Month",
        ylabel="Total Distance (km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_cumulative_distance_over_time(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Cumulative distance per month:
    - x-axis: ['Jan', 'Feb', ..., 'Dec']
    - y-axis: cumulative distance (km)
    - Separate line per year
    """
    data = utils.prepare_dated_activities(activities_df)
    monthly_df = data.groupby(["year", "month"])["distance_km"].sum().reset_index()

    def plot_fn(axis):
        for year in sorted(monthly_df["year"].unique()):
            sub = monthly_df[monthly_df["year"] == year].copy()
            sub = sub.set_index("month").reindex(range(1, 13), fill_value=0).reset_index()
            sub["cum_dist"] = sub["distance_km"].cumsum()
            axis.plot(sub["month"], sub["cum_dist"], marker="o", label=str(year))
        utils.label_month_axis(axis)
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Cumulative Distance per Year",
        xlabel="Month",
        ylabel="Cumulative Distance (km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_monthly_distance_by_year_grouped(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Clustered bar chart comparing total monthly distance by year.
    - X-axis: Month (Jan–Dec)
    - Y-axis: Total distance (km)
    - Grouped by year
    """
    data = utils.prepare_dated_activities(activities_df)
    grouped = data.groupby(["month", "year"])["distance_km"].sum().reset_index()

    pivot = grouped.pivot(index="month", columns="year", values="distance_km").fillna(0)
    pivot = pivot.sort_index()
    month_labels = [calendar.month_abbr[m] for m in pivot.index]

    def plot_fn(axis):
        pivot.plot(kind="bar", width=0.8, ax=axis)
        axis.set_xticks(range(len(month_labels)))
        axis.set_xticklabels(month_labels, rotation=45)
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Year-over-Year Monthly Distance Comparison",
        xlabel="Month",
        ylabel="Total Distance (km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_rolling_distance(activities_df: pd.DataFrame, output_path: str, window: int = 30) -> None:
    """
    Line graph showing rolling X-day distance total.
    Default window = 30 days.
    """
    data = utils.prepare_dated_activities(activities_df)
    daily = data.groupby("start_date")["distance_km"].sum().reset_index()
    daily["rolling_distance_km"] = daily["distance_km"].rolling(window=window).sum()

    def plot_fn(axis):
        axis.plot(daily["start_date"], daily["rolling_distance_km"], color="blue", linewidth=2)

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title=f"Rolling {window}-Day Distance",
        xlabel="Date",
        ylabel="Distance (km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def plot_longest_run_per_month(activities_df: pd.DataFrame, output_path: str) -> None:
    """
    Scatter plot of longest run per month across all years.
    - X-axis: month (Jan–Dec)
    - Y-axis: longest run (km)
    - Points: one per year-month, only if a run occurred
    - Colour-coded by year
    """
    data = utils.prepare_dated_activities(activities_df)
    longest = data.groupby(["year", "month"])["distance_km"].max().reset_index()

    def plot_fn(axis):
        for year in sorted(longest["year"].unique()):
            year_data = longest[longest["year"] == year]
            axis.scatter(
                year_data["month"],
                year_data["distance_km"],
                label=str(year),
                alpha=0.7,
                s=60,
            )
        utils.label_month_axis(axis)
        axis.legend(title="Year")

    # pylint: disable=R0801
    utils.plot_with_common_setup(
        title="Longest Run per Month",
        xlabel="Month",
        ylabel="Distance (km)",
        output_path=output_path,
        plot_func=plot_fn,
    )
    # pylint: enable=R0801


def build_monthly_distance_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive version of total distance run by month."""
    data = monthly_distance(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="month_start",
        y="distance_km",
        markers=True,
        labels={"month_start": "Month", "distance_km": "Distance (km)"},
        hover_data={"month_start": "|%B %Y", "distance_km": ":.1f"},
    )
    return interactive_utils.apply_layout(figure, "Monthly distance", "Distance (km)")


def build_monthly_distance_by_year_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive year-over-year monthly distance comparison."""
    data = monthly_distance(activities_df)
    if data.empty:
        return go.Figure()
    month_names = list(calendar.month_abbr)[1:]
    data["month_name"] = pd.Categorical(
        data["month"].map(dict(enumerate(month_names, start=1))),
        categories=month_names,
        ordered=True,
    )
    data = data.sort_values(["year", "month"])
    figure = px.line(
        data,
        x="month_name",
        y="distance_km",
        color=data["year"].astype(str),
        markers=True,
        category_orders={"month_name": month_names},
        labels={"month_name": "Month", "distance_km": "Distance (km)", "color": "Year"},
        hover_data={"year": True, "distance_km": ":.1f"},
    )
    figure.update_xaxes(categoryorder="array", categoryarray=month_names)
    return interactive_utils.apply_layout(figure, "Monthly distance by year", "Distance (km)")


def build_cumulative_distance_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive cumulative distance chart."""
    data = cumulative_distance(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="activity_date",
        y="cumulative_distance_km",
        labels={"activity_date": "Date", "cumulative_distance_km": "Distance (km)"},
        hover_data={"activity_date": "|%d %B %Y", "cumulative_distance_km": ":.1f"},
    )
    return interactive_utils.apply_layout(figure, "Cumulative distance", "Distance (km)")


def build_rolling_distance_figure(activities_df: pd.DataFrame, window_days: int = 30) -> go.Figure:
    """Build an interactive rolling distance chart."""
    data = rolling_distance(activities_df, window_days=window_days)
    if data.empty:
        return go.Figure()
    figure = px.line(
        data,
        x="activity_date",
        y="rolling_distance_km",
        labels={"activity_date": "Date", "rolling_distance_km": "Distance (km)"},
        hover_data={"activity_date": "|%d %B %Y", "rolling_distance_km": ":.1f"},
    )
    return interactive_utils.apply_layout(
        figure, f"Rolling {window_days}-day distance", "Distance (km)"
    )


def build_longest_run_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive longest-run-per-month chart."""
    data = longest_run_by_month(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.bar(
        data,
        x="month_start",
        y="distance_km",
        hover_name="name",
        labels={"month_start": "Month", "distance_km": "Distance (km)"},
        hover_data={"activity_date": "|%d %B %Y", "distance_km": ":.2f"},
    )
    return interactive_utils.apply_layout(figure, "Longest run per month", "Distance (km)")


def build_time_distance_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive time-taken-over-distance chart."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()
    data = data[data["distance_km"] >= 0.5].copy()
    data["moving_time_minutes"] = data["moving_time_s"] / 60.0
    figure = px.scatter(
        data,
        x="distance_km",
        y="moving_time_minutes",
        color=data["year"].astype(str),
        hover_name="name",
        labels={
            "distance_km": "Distance (km)",
            "moving_time_minutes": "Moving time (minutes)",
            "color": "Year",
        },
        hover_data={"activity_date": "|%d %B %Y", "distance_km": ":.2f"},
    )
    interactive_utils.add_linear_trend(figure, data["distance_km"], data["moving_time_minutes"])
    return interactive_utils.apply_layout(
        figure, "Time taken over distance", "Moving time (minutes)"
    )


def build_number_of_runs_by_distance_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive number-of-runs-per-distance chart."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()
    data["distance_bucket"] = data["distance_km"].round().astype(int)
    grouped = data.groupby("distance_bucket", as_index=False).size()
    grouped = grouped.rename(columns={"size": "runs"})
    figure = px.bar(
        grouped,
        x="distance_bucket",
        y="runs",
        labels={"distance_bucket": "Rounded distance (km)", "runs": "Runs"},
    )
    return interactive_utils.apply_layout(figure, "Number of runs per distance", "Runs")


def build_pace_vs_total_distance_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive running-pace-versus-total-distance chart."""
    data = prepare_splits(splits_df)
    if data.empty:
        return go.Figure()
    grouped = data.groupby(["activity_id", "activity_date"], as_index=False).agg(
        distance_m=("distance_m", "sum"),
        elapsed_time_s=("elapsed_time_s", "sum"),
    )
    grouped["distance_km"] = grouped["distance_m"] / 1000.0
    valid_distance = grouped["distance_km"].where(grouped["distance_km"] > 0)
    grouped["pace_sec_km"] = grouped["elapsed_time_s"] / valid_distance
    grouped = grouped.replace([np.inf, -np.inf], np.nan).dropna(subset=["pace_sec_km"])
    figure = px.scatter(
        grouped,
        x="distance_km",
        y="pace_sec_km",
        labels={"distance_km": "Distance (km)", "pace_sec_km": "Pace"},
        hover_data={"activity_date": "|%d %B %Y", "activity_id": True},
    )
    interactive_utils.add_linear_trend(figure, grouped["distance_km"], grouped["pace_sec_km"])
    interactive_utils.apply_layout(figure, "Running pace vs total distance")
    return interactive_utils.apply_pace_axis(figure, grouped["pace_sec_km"])
