"""Activity explorer page for the Strava dashboard."""

import pandas as pd
import streamlit as st

from dashboard.formatting import format_duration, format_pace, rounded_numeric
from strava_data.strava_api.processing.analytics import (
    activity_heart_rate_summary,
    prepare_splits,
)


def render(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """Render the activity table and split explorer."""
    st.header("Activity explorer")
    activities = activity_heart_rate_summary(activities_df, splits_df).sort_values(
        "activity_date", ascending=False
    )
    splits = prepare_splits(splits_df)
    if activities.empty:
        st.info("No activities match the current filters.")
        return

    display = activities.copy()
    display["Date"] = display["activity_date"].dt.strftime("%d %b %Y")
    display["Activity"] = display["name"]
    display["Distance (km)"] = display["distance_km"].round(2)
    display["Moving time"] = display["moving_time_s"].map(format_duration)
    display["Pace"] = display["pace_sec_km"].map(format_pace)
    display["Elevation (m)"] = rounded_numeric(display["total_elevation_gain_m"])
    display["Cadence"] = rounded_numeric(
        display["average_cadence"], decimals=1, zero_as_missing=True
    )
    columns = [
        "Date",
        "Activity",
        "Distance (km)",
        "Moving time",
        "Pace",
        "Elevation (m)",
        "Cadence",
    ]
    if "average_heartrate" in display.columns:
        display["Average HR"] = rounded_numeric(display["average_heartrate"])
        columns.append("Average HR")
    if "max_heartrate" in display.columns:
        display["Maximum HR"] = rounded_numeric(display["max_heartrate"])
        columns.append("Maximum HR")
    st.dataframe(
        display[columns],
        hide_index=True,
        width="stretch",
        column_config={
            "Average HR": st.column_config.NumberColumn(
                "Average HR",
                help="Activity average, or a moving-time-weighted split average for older runs.",
                format="%.0f bpm",
            ),
            "Maximum HR": st.column_config.NumberColumn(
                "Maximum HR",
                help=(
                    "Activity maximum when available. For older runs, this is the highest "
                    "kilometre-split average."
                ),
                format="%.0f bpm",
            ),
        },
    )
    if activities["max_heartrate_from_splits"].any():
        st.caption(
            "For older activities without activity-level heart-rate fields, average HR is "
            "weighted from the splits and maximum HR is the highest split average."
        )

    activity_options = {
        f"{row.activity_date:%d %b %Y} — {row.name} ({row.distance_km:.2f} km)": row.activity_id
        for row in activities.itertuples()
    }
    selected_label = st.selectbox("Inspect kilometre splits", options=list(activity_options))
    activity_id = activity_options[selected_label]
    activity_splits = splits[splits["activity_id"] == activity_id].copy()
    if activity_splits.empty:
        st.info("No split data are available for this activity.")
        return

    activity_splits["Split"] = activity_splits["split_index"].astype("Int64")
    activity_splits["Distance"] = activity_splits["distance_km"].map(
        lambda value: f"{value:.2f} km"
    )
    activity_splits["Pace"] = activity_splits["pace_sec_km"].map(format_pace)
    activity_splits["Elevation"] = activity_splits["elevation_difference_m"].map(
        lambda value: f"{value:+.0f} m"
    )
    split_columns = ["Split", "Distance", "Pace", "Elevation"]
    if activity_splits["average_heartrate"].notna().any():
        activity_splits["Heart rate"] = rounded_numeric(activity_splits["average_heartrate"])
        split_columns.append("Heart rate")
    st.dataframe(activity_splits[split_columns], hide_index=True, width="stretch")
