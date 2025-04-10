"""
Data classes or schemas representing Strava data in Python.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Activity:
    # pylint: disable=too-many-instance-attributes
    """
    Represents a single Strava activity row.
    """

    activity_id: int
    name: str
    activity_type: str
    distance_m: float
    moving_time_s: int
    average_speed_m_s: float
    max_speed_m_s: float
    total_elevation_gain_m: float
    start_date_local: str
    average_cadence: float


@dataclass
class Split:
    # pylint: disable=too-many-instance-attributes
    """
    Represents a single 1 km split from a Strava activity.
    """

    split_id: int
    activity_id: int
    distance_m: float
    elapsed_time_s: int
    elevation_difference_m: float
    moving_time_s: int
    pace_zone: int
    split_index: int
    average_grade_adjusted_speed_m_s: float
    average_heartrate: Optional[float]
    start_date_local: str
