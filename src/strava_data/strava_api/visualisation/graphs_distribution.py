"""
Contains the distribution chart functions, each saving a PNG file.
"""

# pylint: disable=duplicate-code

import calendar
from matplotlib import ticker
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from strava_data.strava_api.processing.analytics import (
    heart_rate_zones,
    pace_over_time,
    prepare_activities,
    run_rest_summary,
)
from strava_data.strava_api.visualisation import interactive_utils, utils


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


def _activity_calendar_year_grid(
    daily: pd.DataFrame, year: int, weekday_order: list[str]
) -> tuple[list[int], np.ndarray, np.ndarray]:
    """Return week numbers, distances and hover data for one calendar year."""
    year_start = pd.Timestamp(year=year, month=1, day=1)
    year_end = pd.Timestamp(year=year, month=12, day=31)
    calendar_data = pd.DataFrame({"activity_date": pd.date_range(year_start, year_end, freq="D")})
    calendar_data = calendar_data.merge(daily, on="activity_date", how="left")
    calendar_data[["distance_km", "activities"]] = calendar_data[
        ["distance_km", "activities"]
    ].fillna(0)
    first_monday = year_start - pd.Timedelta(days=year_start.weekday())
    calendar_data["week"] = ((calendar_data["activity_date"] - first_monday).dt.days // 7) + 1
    calendar_data["weekday"] = calendar_data["activity_date"].dt.day_name()
    calendar_data["date_label"] = calendar_data["activity_date"].dt.strftime("%d %B %Y")

    weeks = list(range(1, int(calendar_data["week"].max()) + 1))
    distance_grid = calendar_data.pivot(
        index="weekday", columns="week", values="distance_km"
    ).reindex(index=weekday_order, columns=weeks)
    activity_grid = calendar_data.pivot(
        index="weekday", columns="week", values="activities"
    ).reindex(index=weekday_order, columns=weeks)
    date_grid = calendar_data.pivot(index="weekday", columns="week", values="date_label").reindex(
        index=weekday_order, columns=weeks
    )
    custom_data = np.empty((*distance_grid.shape, 2), dtype=object)
    custom_data[:, :, 0] = date_grid.fillna("").to_numpy()
    custom_data[:, :, 1] = activity_grid.fillna(0).to_numpy()
    return weeks, distance_grid.to_numpy(), custom_data


def build_activity_heatmap_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build one readable Monday-to-Sunday activity calendar for each year."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()

    daily = data.groupby("activity_date", as_index=False).agg(
        distance_km=("distance_km", "sum"),
        activities=("activity_id", "count"),
    )
    years = sorted(daily["activity_date"].dt.year.unique())
    weekday_order = list(calendar.day_name)
    figure = make_subplots(
        rows=len(years),
        cols=1,
        subplot_titles=[str(year) for year in years],
        vertical_spacing=min(0.08, 0.35 / max(len(years), 1)),
    )

    for row_number, year in enumerate(years, start=1):
        weeks, distance_grid, custom_data = _activity_calendar_year_grid(daily, year, weekday_order)
        figure.add_trace(
            go.Heatmap(
                x=weeks,
                y=weekday_order,
                z=distance_grid,
                customdata=custom_data,
                coloraxis="coloraxis",
                hovertemplate=(
                    "%{customdata[0]}<br>Distance: %{z:.2f} km<br>"
                    "Activities: %{customdata[1]:.0f}<extra></extra>"
                ),
            ),
            row=row_number,
            col=1,
        )
        figure.update_xaxes(
            title_text="Week of year" if row_number == len(years) else "",
            tickmode="linear",
            tick0=1,
            dtick=4,
            row=row_number,
            col=1,
        )
        figure.update_yaxes(
            categoryorder="array",
            categoryarray=weekday_order,
            autorange="reversed",
            row=row_number,
            col=1,
        )

    interactive_utils.apply_layout(figure, "Activity calendar")
    figure.update_layout(
        coloraxis={
            "colorscale": "Blues",
            "colorbar": {"title": "Distance (km)"},
        },
        height=max(360, 150 * len(years)),
        hovermode="closest",
    )
    return figure


def build_run_distance_distribution_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive run-distance distribution chart."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()
    figure = px.histogram(
        data,
        x="distance_km",
        color=data["year"].astype(str),
        barmode="overlay",
        nbins=30,
        labels={"distance_km": "Distance (km)", "count": "Runs", "color": "Year"},
        hover_data={"name": True, "activity_date": "|%d %B %Y"},
    )
    figure.update_traces(opacity=0.65)
    return interactive_utils.apply_layout(figure, "Run distance distribution", "Runs")


def build_pace_distribution_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive one-kilometre pace distribution chart."""
    data = pace_over_time(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.histogram(
        data,
        x="pace_sec_km",
        color=data["year"].astype(str),
        barmode="overlay",
        nbins=35,
        labels={"pace_sec_km": "Pace", "count": "Splits", "color": "Year"},
    )
    figure.update_traces(opacity=0.65)
    tick_values, tick_text = interactive_utils.pace_tick_values(data["pace_sec_km"])
    figure.update_xaxes(title_text="Pace (min/km)", tickvals=tick_values, ticktext=tick_text)
    return interactive_utils.apply_layout(figure, "Pace distribution", "Splits")


def build_elevation_distribution_figure(activities_df: pd.DataFrame) -> go.Figure:
    """Build an interactive elevation-gain distribution chart."""
    data = prepare_activities(activities_df)
    if data.empty:
        return go.Figure()
    data = data[data["total_elevation_gain_m"] > 0]
    figure = px.histogram(
        data,
        x="total_elevation_gain_m",
        color=data["year"].astype(str),
        barmode="overlay",
        nbins=35,
        labels={
            "total_elevation_gain_m": "Elevation gain (m)",
            "count": "Runs",
            "color": "Year",
        },
    )
    figure.update_traces(opacity=0.65)
    return interactive_utils.apply_layout(figure, "Elevation gain distribution", "Runs")


def build_heart_rate_zone_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build an interactive training-intensity-by-heart-rate-zone chart."""
    data = heart_rate_zones(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.bar(
        data,
        x="month_start",
        y="time_minutes",
        color="heart_rate_zone",
        barmode="stack",
        labels={
            "month_start": "Month",
            "time_minutes": "Time (minutes)",
            "heart_rate_zone": "Heart-rate zone",
        },
    )
    return interactive_utils.apply_layout(
        figure, "Training intensity by heart-rate zone", "Time (minutes)"
    )


def build_run_rest_heatmap_figure(activities_df: pd.DataFrame, value: str) -> go.Figure:
    """Build an interactive run-day, rest-day or run-day-ratio heatmap."""
    data = run_rest_summary(activities_df)
    if data.empty:
        return go.Figure()
    allowed_values = {
        "run_days": "Run days",
        "rest_days": "Rest days",
        "run_day_ratio": "Run-day ratio",
    }
    if value not in allowed_values:
        raise ValueError(f"Unsupported run/rest heatmap value: {value}")
    pivot = data.pivot(index="year", columns="month", values=value)
    pivot = pivot.reindex(columns=range(1, 13))
    month_names = list(calendar.month_abbr)[1:]
    figure = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=month_names,
            y=pivot.index.astype(str),
            colorbar={"title": allowed_values[value]},
            hovertemplate="Year %{y}<br>%{x}<br>Value %{z:.2f}<extra></extra>",
        )
    )
    figure.update_xaxes(title_text="Month")
    figure.update_yaxes(title_text="Year")
    return interactive_utils.apply_layout(figure, f"{allowed_values[value]} by month")
