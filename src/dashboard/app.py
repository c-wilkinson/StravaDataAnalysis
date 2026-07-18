"""Streamlit entry point for the Parquet-backed Strava dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data_loader import load_dashboard_data
from dashboard.filters import filter_dashboard_data
from dashboard.pages import activities, distance, effort, images, machine_learning, overview, pace


@st.cache_data(show_spinner=False)
def _cached_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load the generated dashboard datasets through Streamlit's cache."""
    return load_dashboard_data()


def _missing_data_page() -> None:
    st.error("Dashboard Parquet files have not been generated yet.")
    st.code("poetry run python src/main.py --skip-fetch", language="bash")
    st.write(
        "The normal Strava run still generates every PNG and now also writes "
        "`data/dashboard/activities.parquet` and `data/dashboard/splits.parquet`."
    )


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title="Strava Analytics", page_icon="🏃", layout="wide")

    activities_df, splits_df, _ = _cached_data()
    if activities_df.empty:
        _missing_data_page()
        return

    def overview_page() -> None:
        filtered_activities, filtered_splits = filter_dashboard_data(activities_df, splits_df)
        overview.render(filtered_activities, filtered_splits)

    def distance_page() -> None:
        filtered_activities, _ = filter_dashboard_data(activities_df, splits_df)
        distance.render(filtered_activities)

    def pace_page() -> None:
        _, filtered_splits = filter_dashboard_data(activities_df, splits_df)
        pace.render(filtered_splits)

    def effort_page() -> None:
        filtered_activities, filtered_splits = filter_dashboard_data(activities_df, splits_df)
        effort.render(filtered_activities, filtered_splits)

    def machine_learning_page() -> None:
        _, filtered_splits = filter_dashboard_data(activities_df, splits_df)
        machine_learning.render(filtered_splits)

    def activities_page() -> None:
        filtered_activities, filtered_splits = filter_dashboard_data(activities_df, splits_df)
        activities.render(filtered_activities, filtered_splits)

    navigation = st.navigation(
        [
            st.Page(overview_page, title="Overview", default=True),
            st.Page(distance_page, title="Distance"),
            st.Page(pace_page, title="Pace"),
            st.Page(effort_page, title="Effort"),
            st.Page(machine_learning_page, title="Machine learning"),
            st.Page(activities_page, title="Activities"),
            st.Page(images.render, title="Original images"),
        ],
        position="top",
    )

    st.title("Strava Analytics")
    st.caption("Interactive charts alongside the original generated image graphs.")
    navigation.run()


if __name__ == "__main__":
    main()
