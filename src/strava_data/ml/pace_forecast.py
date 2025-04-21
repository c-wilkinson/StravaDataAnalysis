"""
Machine learning to forecast pace
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from strava_data.db.dao import load_all_splits
from strava_data.strava_api.visualisation.utils import (
    prepare_dated_activities,
    format_pace,
    save_and_close_plot,
)
from utils.logger import get_logger

LOGGER = get_logger()

def build_weekly_pace_features(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates ~1 km splits into weekly median pace and rolling stats.
    """
    data = prepare_dated_activities(splits_df)
    data = data[(data["distance_m"] >= 950) & (data["distance_m"] <= 1050)]
    data["start_date"] = pd.to_datetime(data["start_date_local"]).dt.tz_localize(None)
    data["week"] = data["start_date"].dt.to_period("W").apply(lambda r: r.start_time)
    data["pace_sec_km"] = data["elapsed_time_s"] / (data["distance_m"] / 1000)

    grouped = (
        data.groupby("week")
        .agg(
            pace_median=("pace_sec_km", "median"),
            pace_std=("pace_sec_km", "std"),
            split_count=("pace_sec_km", "count"),
        )
        .reset_index()
        .dropna()
    )

    grouped["pace_7d_avg"] = grouped["pace_median"].rolling(window=2).mean()
    grouped["pace_7d_std"] = grouped["pace_median"].rolling(window=2).std()
    grouped = grouped.dropna()

    return grouped

def train_forecast_model(data: pd.DataFrame):
    """
    Trains a Ridge regression model using time-based cross-validation.
    """
    features = data[["pace_7d_avg", "pace_7d_std", "split_count"]]
    target = data["pace_median"]

    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])

    tscv = TimeSeriesSplit(n_splits=5)
    scores = cross_val_score(
        model, features, target, cv=tscv, scoring="neg_root_mean_squared_error"
    )
    LOGGER.info("CV RMSE: %.2f seconds", -scores.mean())

    model.fit(features, target)
    return model

def predict_next_week(model, latest_row: pd.Series):
    """
    Uses trained model to predict next week's average pace.
    """
    next_features = latest_row[["pace_7d_avg", "pace_7d_std", "split_count"]].to_frame().T
    predicted_pace = model.predict(next_features)[0]
    minutes = int(predicted_pace // 60)
    seconds = int(predicted_pace % 60)
    LOGGER.info("Forecasted pace for next week: %d:%02d per km", minutes, seconds)
    return predicted_pace

def plot_forecast(weekly_data: pd.DataFrame, forecast_value: float, output_path: str) -> None:
    """
    Plots weekly median pace and overlays the next week's forecast as an X with RMSE band.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(weekly_data["week"], weekly_data["pace_median"], label="Actual Pace", marker="o")

    true_values = weekly_data["pace_median"]
    feature_values = weekly_data[["pace_7d_avg", "pace_7d_std", "split_count"]]
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
    model.fit(feature_values, true_values)
    residuals = true_values - model.predict(feature_values)
    rmse = np.sqrt(np.mean(residuals**2))

    forecast_week = weekly_data["week"].max() + pd.Timedelta(weeks=1)
    plt.scatter(
        forecast_week,
        forecast_value,
        marker="x",
        color="red",
        s=100,
        label="Forecast Next Week"
    )

    plt.fill_between(
        weekly_data["week"].astype("datetime64[ns]"),
        weekly_data["pace_median"] - rmse,
        weekly_data["pace_median"] + rmse,
        color="blue",
        alpha=0.1,
        label="±1 RMSE Band",
    )

    plt.title("Weekly Median Pace with Forecast")
    plt.xlabel("Week")
    plt.ylabel("Pace (mm:ss)")
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_pace))
    plt.legend()
    plt.grid(True)
    save_and_close_plot(output_path)

def run_forecast_pipeline():
    """
    Orchestrates weekly pace forecast: feature prep, training, prediction, plotting.
    """
    LOGGER.info("Building features from splits...")
    splits_df = load_all_splits()
    weekly_data = build_weekly_pace_features(splits_df)

    LOGGER.info("Training forecast model...")
    model = train_forecast_model(weekly_data)

    LOGGER.info("Predicting future pace...")
    latest_features = weekly_data.iloc[-1]
    forecast_value = predict_next_week(model, latest_features)

    LOGGER.info("Generating forecast chart...")
    plot_forecast(weekly_data, forecast_value, "Forecast_Weekly_Pace.png")

if __name__ == "__main__":
    run_forecast_pipeline()
