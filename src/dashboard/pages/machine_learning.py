"""Machine-learning page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.page_utils import render_figure
from dashboard.paths import ASSETS_DIRECTORY
from strava_data.strava_api.visualisation import graphs_ml


def render(splits_df: pd.DataFrame) -> None:
    """Render forecast and clustering charts from the exported split data."""
    st.header("Machine learning")
    if splits_df.empty:
        st.info("No split data match the current filters.")
        return

    st.caption("Interactive equivalents of the existing forecast and run-clustering images.")
    render_figure(
        graphs_ml.build_pace_forecast_figure(splits_df),
        "At least three complete weeks of split data are needed for the pace forecast.",
    )
    left, right = st.columns(2)
    with left:
        render_figure(
            graphs_ml.build_run_cluster_figure(splits_df),
            "At least four activities with three or more kilometre splits are needed.",
        )
    with right:
        render_figure(graphs_ml.build_run_type_distribution_figure(splits_df))

    training_plan_path = ASSETS_DIRECTORY / "A.I._Recommended_Training.png"
    if training_plan_path.exists():
        st.subheader("Recommended training")
        st.image(str(training_plan_path), width="stretch")
