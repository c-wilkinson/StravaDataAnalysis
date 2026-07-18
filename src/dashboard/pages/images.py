"""Original PNG gallery page for the Strava dashboard."""

import streamlit as st

from dashboard.paths import ASSETS_DIRECTORY


def render() -> None:
    """Render the unchanged Matplotlib and Seaborn image output."""
    st.header("Original image graphs")
    st.caption(
        "The existing PNG output is unchanged. The historical start-time graph remains available "
        "here, but precise start times are not present in the dashboard Parquet files."
    )
    image_files = sorted(ASSETS_DIRECTORY.glob("*.png"), key=lambda path: path.name.lower())
    if not image_files:
        st.info("Run `poetry run python src/main.py --skip-fetch` to generate the PNG images.")
        return

    query = (
        st.text_input("Filter images", placeholder="Pace, distance, training...").strip().lower()
    )
    if query:
        image_files = [path for path in image_files if query in path.stem.lower()]
    for index in range(0, len(image_files), 2):
        columns = st.columns(2)
        for offset, image_path in enumerate(image_files[index : index + 2]):
            with columns[offset]:
                caption = image_path.stem.replace("_", " ")
                st.image(str(image_path), caption=caption, width="stretch")
