"""
Machine learning to classify run types (e.g. Easy, Tempo, Intervals, Long)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from strava_data.db.dao import load_all_splits
from strava_data.ml.utils import prepare_pace_summary
from strava_data.strava_api.visualisation.utils import (
    prepare_dated_activities,
    save_and_close_plot,
    format_pace,
)
from utils.logger import get_logger

LOGGER = get_logger()

RUN_TYPE_LABELS = {
    0: "Easy",
    1: "Tempo",
    2: "Intervals",
    3: "Long",
}


def build_run_features(splits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates split data into per-run features for clustering.
    """
    data = prepare_dated_activities(splits_df)
    data["start_date"] = pd.to_datetime(data["start_date_local"]).dt.tz_localize(None)

    # Group by activity ID and start date to represent each run
    summary = prepare_pace_summary(data, group_cols=["activity_id", "start_date_local"])

    summary["start_date"] = pd.to_datetime(summary["start_date_local"])
    summary["day_of_week"] = summary["start_date"].dt.dayofweek
    summary["month"] = summary["start_date"].dt.month
    summary["year"] = summary["start_date"].dt.year

    return summary


def cluster_run_types(data: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """
    Applies KMeans clustering to classify run types.
    """
    features = data[["distance_km", "pace_median", "pace_std", "split_count"]]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = model.fit_predict(features_scaled)

    score = silhouette_score(features_scaled, cluster_labels)
    LOGGER.info("Silhouette Score: %.3f", score)

    data["run_type_cluster"] = cluster_labels
    data["run_type"] = data["run_type_cluster"].map(RUN_TYPE_LABELS)
    return data


def plot_clusters(data: pd.DataFrame, output_path: str) -> None:
    """
    Scatterplot of distance vs. pace coloured by run type.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=data,
        x="distance_km",
        y="pace_median",
        hue="run_type",
        palette="tab10",
        alpha=0.8,
    )
    plt.title("Run Type Clustering")
    plt.xlabel("Distance (km)")
    plt.ylabel("Pace (mm:ss per km)")
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_pace))
    plt.grid(True)
    plt.legend(title="Run Type")
    save_and_close_plot(output_path)


def plot_run_type_distribution_by_year(data: pd.DataFrame, output_path: str) -> None:
    """
    Bar chart showing count of run types per year.
    """
    counts = data.groupby(["year", "run_type"]).size().reset_index(name="count")
    pivot = counts.pivot(index="year", columns="run_type", values="count").fillna(0)

    pivot.plot(kind="bar", stacked=True, figsize=(10, 6), colormap="tab10")
    plt.title("Run Type Distribution by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Runs")
    plt.xticks(rotation=45)
    plt.legend(title="Run Type")
    plt.grid(True, axis="y")
    save_and_close_plot(output_path)


def run_clustering_pipeline():
    """
    Runs the full clustering pipeline: feature prep, clustering, and visualisation.
    """
    LOGGER.info("Loading and building features...")
    splits_df = load_all_splits()
    feature_data = build_run_features(splits_df)

    LOGGER.info("Running KMeans clustering...")
    clustered = cluster_run_types(feature_data, n_clusters=4)

    LOGGER.info("Plotting clusters...")
    plot_clusters(clustered, "Run_Type_Clusters.png")

    LOGGER.info("Plotting run type distribution...")
    plot_run_type_distribution_by_year(clustered, "Run_Type_Distribution_By_Year.png")

    return clustered


if __name__ == "__main__":
    run_clustering_pipeline()
