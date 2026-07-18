"""Pace and performance page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.page_utils import render_figure
from strava_data.strava_api.visualisation import (
    graphs_distance,
    graphs_distribution,
    graphs_pace,
)


def render(splits_df: pd.DataFrame) -> None:
    """Render interactive pace charts."""
    st.header("Pace and performance")
    if splits_df.empty:
        st.info("No split data match the current filters.")
        return

    trends, relationships, distribution = st.tabs(["Trends", "Relationships", "Distribution"])
    with trends:
        render_figure(graphs_pace.build_running_pace_figure(splits_df))
        render_figure(graphs_pace.build_fastest_1km_pace_figure(splits_df))
        render_figure(graphs_pace.build_median_1km_pace_figure(splits_df))
        render_figure(graphs_pace.build_pace_variability_figure(splits_df))
    with relationships:
        render_figure(graphs_distance.build_pace_vs_total_distance_figure(splits_df))
        render_figure(graphs_pace.build_pace_vs_elevation_figure(splits_df))
        render_figure(graphs_pace.build_pace_by_day_figure(splits_df))
    with distribution:
        render_figure(graphs_distribution.build_pace_distribution_figure(splits_df))
