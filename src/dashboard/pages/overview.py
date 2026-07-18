"""Overview page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.formatting import format_duration, format_pace
from dashboard.page_utils import render_figure
from strava_data.strava_api.processing.analytics import prepare_activities, prepare_splits
from strava_data.strava_api.visualisation import graphs_distance


def _render_metrics(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    activities = prepare_activities(activities_df)
    splits = prepare_splits(splits_df)
    total_distance = activities["distance_km"].sum()
    total_time = activities["moving_time_s"].sum()
    total_elevation = activities["total_elevation_gain_m"].sum()
    weighted_pace = total_time / total_distance if total_distance > 0 else float("nan")
    average_heart_rate = splits["average_heartrate"].mean() if not splits.empty else float("nan")

    first_row = st.columns(5)
    first_row[0].metric("Activities", f"{len(activities):,}")
    first_row[1].metric("Distance", f"{total_distance:,.1f} km")
    first_row[2].metric("Moving time", format_duration(total_time))
    first_row[3].metric("Elevation", f"{total_elevation:,.0f} m")
    first_row[4].metric("Average pace", format_pace(weighted_pace))

    second_row = st.columns(4)
    second_row[0].metric("Longest activity", f"{activities['distance_km'].max():.2f} km")
    second_row[1].metric("Latest activity", activities["activity_date"].max().strftime("%d %b %Y"))
    second_row[2].metric(
        "Average heart rate",
        f"{average_heart_rate:.0f} bpm" if pd.notna(average_heart_rate) else "—",
    )
    second_row[3].metric("Active years", f"{activities['year'].nunique():,}")


def render(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """Render the overview page."""
    st.header("Overview")
    if activities_df.empty:
        st.info("No activities match the current filters.")
        return

    _render_metrics(activities_df, splits_df)
    left, right = st.columns(2)
    with left:
        render_figure(graphs_distance.build_monthly_distance_figure(activities_df))
    with right:
        render_figure(graphs_distance.build_rolling_distance_figure(activities_df))

    st.subheader("Recent activities")
    activities = prepare_activities(activities_df).sort_values("activity_date", ascending=False)
    display = activities.head(20).copy()
    display["Date"] = display["activity_date"].dt.strftime("%d %b %Y")
    display["Activity"] = display["name"]
    display["Distance"] = display["distance_km"].map(lambda value: f"{value:.2f} km")
    display["Time"] = display["moving_time_s"].map(format_duration)
    display["Pace"] = display["pace_sec_km"].map(format_pace)
    display["Elevation"] = display["total_elevation_gain_m"].map(lambda value: f"{value:.0f} m")
    st.dataframe(
        display[["Date", "Activity", "Distance", "Time", "Pace", "Elevation"]],
        hide_index=True,
        width="stretch",
    )
