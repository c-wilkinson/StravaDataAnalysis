"""
Main entry point for running Strava data retrieval, processing, and visualization.
"""

import pandas as pd

from utils.logger import get_logger
from strava_data.auth import get_or_refresh_tokens
from strava_data.db.dao import (
    decrypt_database,
    encrypt_database,
    init_database,
    insert_activities,
    insert_splits,
    load_all_activities,
    load_all_splits,
)
from strava_data.strava_api.client import fetch_activities, fetch_splits_if_needed
from strava_data.strava_api.processing.transform import transform_activities, transform_splits
from strava_data.strava_api.visualisation import graphs

LOGGER = get_logger()


def main() -> None:
    """
    1. Authenticates or refreshes Strava tokens.
    2. Initializes the database if needed.
    3. Fetches new activities from Strava and their splits.
    4. Transforms and stores them in the database.
    5. Generates the graphs using all data from the database.
    """
    LOGGER.info("Start main.")
    decrypt_database()
    init_database()
    get_or_refresh_tokens()

    new_activities = fetch_activities(per_page=50)
    if not new_activities.empty:
        LOGGER.info("New activities detected, processing...")
        new_splits = fetch_splits_if_needed(new_activities)
        transformed_activities = transform_activities(new_activities)
        transformed_splits = transform_splits(new_splits)
        insert_activities(transformed_activities)
        insert_splits(transformed_splits)
        LOGGER.info("New activities processed")
    else:
        LOGGER.info("No new activities detected")

    all_activities = load_all_activities()
    all_splits = load_all_splits()
    generate_required_charts(all_activities, all_splits)
    encrypt_database()
    LOGGER.info("Done.")


def generate_required_charts(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """
    Produces the charts from the specified DataFrames.

    :param activities_df: DataFrame of Strava activities.
    :param splits_df: DataFrame of 1 km splits from those activities.
    """
    LOGGER.info("Generate Running_Pace_vs_Elevation_Change")
    graphs.plot_pace_vs_elevation_change(splits_df, "Running_Pace_vs_Elevation_Change.png")
    LOGGER.info("Generate Time_Taken_Distance")
    graphs.plot_time_taken_over_distances(activities_df, "Time_Taken_Distance.png")
    LOGGER.info("Generate Running_Pace_over_Time")
    graphs.plot_running_pace_over_time(splits_df, "Running_Pace_over_Time.png")
    LOGGER.info("Generate Running_Pace_vs_Total_Distance")
    graphs.plot_pace_vs_total_distance(splits_df, "Running_Pace_vs_Total_Distance.png")
    LOGGER.info("Generate Number_of_Runs_per_Distance")
    graphs.plot_number_of_runs_per_distance(activities_df, "Number_of_Runs_per_Distance.png")
    LOGGER.info("Generate Fastest_1k_Pace_over_Time")
    graphs.plot_fastest_1km_pace_over_time(splits_df, "Fastest_1k_Pace_over_Time.png")
    LOGGER.info("Generate Median_1k_Pace_over_Time")
    graphs.plot_median_1km_pace_over_time(splits_df, "Median_1k_Pace_over_Time.png")
    LOGGER.info("Generate Total_Distance_Ran_by_Month")
    graphs.plot_total_distance_by_month(activities_df, "Total_Distance_Ran_by_Month.png")
    LOGGER.info("Generate Pace_by_Day")
    graphs.plot_pace_by_day_of_week(splits_df, "Pace_by_Day.png")
    LOGGER.info("Generate Activity_Heatmap")
    graphs.plot_heatmap_activities(activities_df, "Activity_Heatmap.png")
    LOGGER.info("Generate Cumulative_Distance")
    graphs.plot_cumulative_distance_over_time(activities_df, "Cumulative_Distance.png")
    LOGGER.info("Generate Longest_Run_per_Month")
    graphs.plot_longest_run_per_month(activities_df, "Longest_Run_per_Month.png")
    LOGGER.info("Generate Elevation_Gain_per_KM_by_Month")
    graphs.plot_elevation_gain_per_km_by_month(activities_df, "Elevation_Gain_per_KM_by_Month.png")
    LOGGER.info("Generate Run_Start_Time_by_Month")
    graphs.plot_run_start_time_distribution(activities_df, "Run_Start_Time_by_Month.png")
    LOGGER.info("Generate Monthly_Distance_by_Year")
    graphs.plot_monthly_distance_by_year_grouped(activities_df, "Monthly_Distance_by_Year.png")
    LOGGER.info("Generate Rolling_30_Day_Comparison")
    graphs.plot_rolling_distance(activities_df, "Rolling_30_Day_Comparison.png", window=30)
    LOGGER.info("Generate Cadence_Over_Time")
    graphs.plot_cadence_over_time(activities_df, "Cadence_Over_Time.png")
    LOGGER.info("Generate Training_Intensity_by_HeartRate_Zone")
    graphs.plot_heart_rate_zone_distribution(splits_df, "Training_Intensity_by_HeartRate_Zone.png")


if __name__ == "__main__":
    main()
