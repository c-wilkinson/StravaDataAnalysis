"""
Main entry point for running Strava data retrieval, processing, and visualization.
"""

import argparse
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
from strava_data.strava_api.visualisation import (
    graphs_distribution,
    graphs_distance,
    graphs_pace,
    graphs_effort,
)
from strava_data.strava_api.visualisation.utils import configure_matplotlib_styles
from strava_data.ml.pace_forecast import run_forecast_pipeline
from strava_data.ml.run_type_classifier import run_clustering_pipeline
from strava_data.ml.training_advisor import generate_training_plan_chart

configure_matplotlib_styles()
LOGGER = get_logger()


def main(skip_fetch: bool = False) -> None:
    """
    Orchestrates the full flow: auth, DB prep, fetch, transform, visualize.
    """
    LOGGER.info("Start main.")
    decrypt_database()
    init_database()

    if not skip_fetch:
        process_new_activities()
    else:
        LOGGER.info("Skipping fetch. Using existing database contents.")

    LOGGER.info("Running chart generation...")
    generate_charts_from_db()
    encrypt_database()
    LOGGER.info("Done.")


def process_new_activities() -> None:
    """
    Authenticates and processes newly fetched Strava activities and splits.
    """
    get_or_refresh_tokens()
    new_activities = fetch_activities(per_page=50)

    if new_activities.empty:
        LOGGER.info("No new activities detected")
        return

    LOGGER.info("New activities detected, processing...")
    new_splits = fetch_splits_if_needed(new_activities)
    transformed_activities = transform_activities(new_activities)
    transformed_splits = transform_splits(new_splits)
    insert_activities(transformed_activities)
    insert_splits(transformed_splits)
    LOGGER.info("New activities processed")


def generate_charts_from_db() -> None:
    """
    Loads all data from the database and triggers chart generation.
    """
    all_activities = load_all_activities()
    all_splits = load_all_splits()
    generate_required_charts(all_activities, all_splits)
    LOGGER.info("Running pace forecast pipeline...")
    run_forecast_pipeline(all_splits)
    LOGGER.info("Running run type clustering pipeline...")
    run_clustering_pipeline(all_splits)
    LOGGER.info("Generating training plan...")
    generate_training_plan_chart(all_activities, all_splits, "A.I._Recommended_Training.png.png")


def generate_required_charts(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    """
    Produces visualisations from activity and split data.
    """
    generate_pace_and_distance_charts(activities_df, splits_df)
    generate_distribution_and_heatmaps(activities_df, splits_df)
    generate_time_series_and_trends(activities_df, splits_df)


def generate_pace_and_distance_charts(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    LOGGER.info("Generate Running_Pace_vs_Elevation_Change")
    graphs_pace.plot_pace_vs_elevation_change(splits_df, "Running_Pace_vs_Elevation_Change.png")
    LOGGER.info("Generate Time_Taken_Distance")
    graphs_distance.plot_time_taken_over_distances(activities_df, "Time_Taken_Distance.png")
    LOGGER.info("Generate Running_Pace_over_Time")
    graphs_pace.plot_running_pace_over_time(splits_df, "Running_Pace_over_Time.png")
    LOGGER.info("Generate Running_Pace_vs_Total_Distance")
    graphs_distance.plot_pace_vs_total_distance(splits_df, "Running_Pace_vs_Total_Distance.png")
    LOGGER.info("Generate Number_of_Runs_per_Distance")
    graphs_distance.plot_number_of_runs_per_distance(
        activities_df, "Number_of_Runs_per_Distance.png"
    )
    LOGGER.info("Generate Fastest_1k_Pace_over_Time")
    graphs_pace.plot_fastest_1km_pace_over_time(splits_df, "Fastest_1k_Pace_over_Time.png")
    LOGGER.info("Generate Median_1k_Pace_over_Time")
    graphs_pace.plot_median_1km_pace_over_time(splits_df, "Median_1k_Pace_over_Time.png")
    LOGGER.info("Generate Total_Distance_Ran_by_Month")
    graphs_distance.plot_total_distance_by_month(activities_df, "Total_Distance_Ran_by_Month.png")
    LOGGER.info("Generate Pace_by_Day")
    graphs_pace.plot_pace_by_day_of_week(splits_df, "Pace_by_Day.png")


def generate_distribution_and_heatmaps(
    activities_df: pd.DataFrame, splits_df: pd.DataFrame
) -> None:
    LOGGER.info("Generate Activity_Heatmap")
    graphs_distribution.plot_heatmap_activities(activities_df, "Activity_Heatmap.png")
    LOGGER.info("Generate Run_Distance_Distribution")
    graphs_distribution.plot_run_distance_distribution(
        activities_df, "Run_Distance_Distribution.png"
    )
    LOGGER.info("Generate Pace_Distribution")
    graphs_distribution.plot_pace_distribution(splits_df, "Pace_Distribution.png")
    LOGGER.info("Generate Elevation_Gain_Distribution")
    graphs_distribution.plot_elevation_gain_distribution(
        activities_df, "Elevation_Gain_Distribution.png"
    )
    LOGGER.info("Generate Run_Days_Heatmap")
    graphs_distribution.plot_run_days_heatmap(activities_df, "Run_Days_Heatmap.png")
    LOGGER.info("Generate Rest_Days_Heatmap")
    graphs_distribution.plot_rest_days_heatmap(activities_df, "Rest_Days_Heatmap.png")
    LOGGER.info("Generate Run_Rest_Ratio_Heatmap")
    graphs_distribution.plot_run_rest_ratio_heatmap(activities_df, "Run_Rest_Ratio_Heatmap.png")


def generate_time_series_and_trends(activities_df: pd.DataFrame, splits_df: pd.DataFrame) -> None:
    LOGGER.info("Generate Cumulative_Distance")
    graphs_distance.plot_cumulative_distance_over_time(activities_df, "Cumulative_Distance.png")
    LOGGER.info("Generate Longest_Run_per_Month")
    graphs_distance.plot_longest_run_per_month(activities_df, "Longest_Run_per_Month.png")
    LOGGER.info("Generate Elevation_Gain_per_KM_by_Month")
    graphs_effort.plot_elevation_gain_per_km_by_month(
        activities_df, "Elevation_Gain_per_KM_by_Month.png"
    )
    LOGGER.info("Generate Run_Start_Time_by_Month")
    graphs_distribution.plot_run_start_time_distribution(
        activities_df, "Run_Start_Time_by_Month.png"
    )
    LOGGER.info("Generate Monthly_Distance_by_Year")
    graphs_distance.plot_monthly_distance_by_year_grouped(
        activities_df, "Monthly_Distance_by_Year.png"
    )
    LOGGER.info("Generate Rolling_30_Day_Comparison")
    graphs_distance.plot_rolling_distance(activities_df, "Rolling_30_Day_Comparison.png", window=30)
    LOGGER.info("Generate Cadence_Over_Time")
    graphs_effort.plot_cadence_over_time(activities_df, "Cadence_Over_Time.png")
    LOGGER.info("Generate Training_Intensity_by_HeartRate_Zone")
    graphs_distribution.plot_heart_rate_zone_distribution(
        splits_df, "Training_Intensity_by_HeartRate_Zone.png"
    )
    LOGGER.info("Generate Pace_Consistency_by_Run")
    graphs_pace.plot_pace_variability_per_run(splits_df, "Pace_Consistency_by_Run.png")
    LOGGER.info("Generate Training_Load_Over_Time")
    graphs_effort.plot_effort_score_over_time(activities_df, "Training_Load_Over_Time.png")
    LOGGER.info("Generate VO2_Proxy_Over_Time")
    graphs_effort.plot_vo2_proxy_over_time(splits_df, "VO2_Proxy_Over_Time.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and visualize Strava data.")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching new activities.")
    args = parser.parse_args()
    main(skip_fetch=args.skip_fetch)
