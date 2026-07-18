"""Global Streamlit filters for the exported running datasets."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from strava_data.strava_api.processing.analytics import (
    filter_run_data,
    prepare_activities,
)


def filter_dashboard_data(
    activities: pd.DataFrame, splits: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Render date and distance filters and return matching running data."""
    run_activities, run_splits = filter_run_data(activities, splits)
    prepared = prepare_activities(run_activities)
    if prepared.empty:
        return run_activities, run_splits

    minimum = prepared["activity_date"].min().date()
    maximum = prepared["activity_date"].max().date()
    selected_dates = st.sidebar.date_input(
        "Activity dates",
        value=(minimum, maximum),
        min_value=minimum,
        max_value=maximum,
    )
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates

    maximum_distance = max(float(prepared["distance_km"].max()), 1.0)
    distance_range = st.sidebar.slider(
        "Distance (km)",
        min_value=0.0,
        max_value=float(round(maximum_distance + 1.0, 1)),
        value=(0.0, float(round(maximum_distance + 1.0, 1))),
        step=0.5,
    )

    mask = prepared["activity_date"].dt.date.between(start_date, end_date) & prepared[
        "distance_km"
    ].between(*distance_range)
    activity_ids = prepared.loc[mask, "activity_id"]
    return (
        run_activities[run_activities["activity_id"].isin(activity_ids)].copy(),
        run_splits[run_splits["activity_id"].isin(activity_ids)].copy(),
    )
