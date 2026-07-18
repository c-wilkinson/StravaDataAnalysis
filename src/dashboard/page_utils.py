"""Shared Streamlit rendering helpers."""

import plotly.graph_objects as go
import streamlit as st


def render_figure(figure: go.Figure, empty_message: str = "No matching data.") -> None:
    """Render a Plotly figure or a useful empty-state message."""
    if not figure.data:
        st.info(empty_message)
        return
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
