"""Effort and recovery page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.page_utils import render_figure
from strava_data.strava_api.visualisation import graphs_distribution, graphs_effort


def render(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """Render effort, elevation, cadence, VO2 and heart-rate charts."""
    st.header("Effort and recovery")
    if activities_df.empty:
        st.info("No activities match the current filters.")
        return

    left, right = st.columns(2)
    with left:
        render_figure(graphs_effort.build_training_load_figure(activities_df))
        render_figure(graphs_effort.build_elevation_per_km_figure(activities_df))
        render_figure(graphs_distribution.build_elevation_distribution_figure(activities_df))
    with right:
        render_figure(graphs_effort.build_cadence_figure(activities_df))
        render_figure(graphs_effort.build_vo2_proxy_figure(splits_df))
        render_figure(graphs_distribution.build_heart_rate_zone_figure(splits_df))
