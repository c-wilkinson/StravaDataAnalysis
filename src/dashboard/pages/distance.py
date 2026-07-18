"""Distance and consistency page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.page_utils import render_figure
from strava_data.strava_api.visualisation import graphs_distance, graphs_distribution


def render(activities_df: pd.DataFrame) -> None:
    """Render distance, consistency and run/rest charts."""
    st.header("Distance and consistency")
    if activities_df.empty:
        st.info("No activities match the current filters.")
        return

    trends, comparisons, distribution, run_rest = st.tabs(
        ["Trends", "Comparisons", "Distribution", "Run and rest"]
    )
    with trends:
        render_figure(graphs_distribution.build_activity_heatmap_figure(activities_df))
        render_figure(graphs_distance.build_cumulative_distance_figure(activities_df))
        render_figure(graphs_distance.build_rolling_distance_figure(activities_df))
        render_figure(graphs_distance.build_longest_run_figure(activities_df))
    with comparisons:
        render_figure(graphs_distance.build_monthly_distance_by_year_figure(activities_df))
        render_figure(graphs_distance.build_time_distance_figure(activities_df))
        render_figure(graphs_distance.build_number_of_runs_by_distance_figure(activities_df))
    with distribution:
        render_figure(graphs_distribution.build_run_distance_distribution_figure(activities_df))
    with run_rest:
        render_figure(graphs_distribution.build_run_rest_heatmap_figure(activities_df, "run_days"))
        render_figure(graphs_distribution.build_run_rest_heatmap_figure(activities_df, "rest_days"))
        render_figure(
            graphs_distribution.build_run_rest_heatmap_figure(activities_df, "run_day_ratio")
        )
