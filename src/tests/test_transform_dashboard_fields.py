"""Tests for fields required by the dashboard export."""

import pandas as pd

from strava_data.strava_api.processing.transform import transform_activities


def test_transform_activities_retains_heart_rate_and_outdoor_flag():
    """New activity writes retain dashboard metrics before database persistence."""
    raw = pd.DataFrame(
        {
            "id": [123],
            "name": ["Treadmill"],
            "type": ["Run"],
            "distance": [5000.0],
            "moving_time": [1500],
            "average_speed": [3.33],
            "max_speed": [4.1],
            "total_elevation_gain": [0.0],
            "start_date_local": ["2026-07-18T10:15:00"],
            "average_cadence": [171.0],
            "average_heartrate": [148.0],
            "max_heartrate": [169.0],
            "trainer": [True],
        }
    )

    result = transform_activities(raw)

    assert result.loc[0, "average_heartrate"] == 148.0
    assert result.loc[0, "max_heartrate"] == 169.0
    assert not bool(result.loc[0, "is_outdoor"])
