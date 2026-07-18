"""Interactive equivalents of the project's machine-learning charts."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from strava_data.strava_api.processing.analytics import one_kilometre_splits
from strava_data.strava_api.visualisation import interactive_utils

RUN_TYPE_LABELS = {0: "Easy", 1: "Tempo", 2: "Intervals", 3: "Long"}


def build_run_features(splits_df: pd.DataFrame) -> pd.DataFrame:
    """Build one row per activity for interactive run-type clustering."""
    splits = one_kilometre_splits(splits_df)
    if splits.empty:
        return pd.DataFrame()
    features = splits.groupby(["activity_id", "activity_date"], as_index=False).agg(
        distance_km=("distance_km", "sum"),
        pace_median=("pace_sec_km", "median"),
        pace_std=("pace_sec_km", "std"),
        split_count=("pace_sec_km", "count"),
    )
    features = features.dropna()
    features["year"] = features["activity_date"].dt.year
    return features


def cluster_runs(splits_df: pd.DataFrame, clusters: int = 4) -> pd.DataFrame:
    """Apply the same KMeans feature set used by the static project charts."""
    data = build_run_features(splits_df)
    if len(data) < clusters:
        return pd.DataFrame()
    feature_columns = ["distance_km", "pace_median", "pace_std", "split_count"]
    feature_values = StandardScaler().fit_transform(data[feature_columns])
    model = KMeans(n_clusters=clusters, random_state=42, n_init=10)
    data = data.copy()
    data["run_type_cluster"] = model.fit_predict(feature_values)
    data["run_type"] = data["run_type_cluster"].map(RUN_TYPE_LABELS)
    return data


def build_run_cluster_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build the interactive distance-versus-pace cluster chart."""
    data = cluster_runs(splits_df)
    if data.empty:
        return go.Figure()
    figure = px.scatter(
        data,
        x="distance_km",
        y="pace_median",
        color="run_type",
        labels={
            "distance_km": "Distance (km)",
            "pace_median": "Median pace",
            "run_type": "Run type",
        },
        hover_data={"activity_date": "|%d %B %Y", "split_count": True, "pace_std": ":.1f"},
    )
    interactive_utils.apply_layout(figure, "Run type clustering")
    return interactive_utils.apply_pace_axis(figure, data["pace_median"])


def build_run_type_distribution_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build the interactive run-type distribution by year chart."""
    data = cluster_runs(splits_df)
    if data.empty:
        return go.Figure()
    counts = data.groupby(["year", "run_type"], as_index=False).size()
    figure = px.bar(
        counts,
        x="year",
        y="size",
        color="run_type",
        barmode="stack",
        labels={"year": "Year", "size": "Runs", "run_type": "Run type"},
    )
    return interactive_utils.apply_layout(figure, "Run type distribution by year", "Runs")


def weekly_pace_forecast(splits_df: pd.DataFrame) -> tuple[pd.DataFrame, float | None]:
    """Fit a Ridge model and return weekly pace history plus the next forecast."""
    splits = one_kilometre_splits(splits_df)
    if splits.empty:
        return pd.DataFrame(), None
    splits["week"] = splits["activity_date"].dt.to_period("W").apply(lambda value: value.start_time)
    weekly = splits.groupby("week", as_index=False).agg(
        pace_median=("pace_sec_km", "median"),
        split_count=("pace_sec_km", "count"),
    )
    weekly = weekly.sort_values("week")
    weekly["pace_7d_avg"] = weekly["pace_median"].rolling(window=2).mean()
    weekly["pace_7d_std"] = weekly["pace_median"].rolling(window=2).std()
    weekly = weekly.dropna().reset_index(drop=True)
    if len(weekly) < 3:
        return weekly, None

    features = weekly[["pace_7d_avg", "pace_7d_std", "split_count"]]
    target = weekly["pace_median"]
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
    model.fit(features, target)
    forecast = float(model.predict(features.tail(1))[0])
    return weekly, forecast


def build_pace_forecast_figure(splits_df: pd.DataFrame) -> go.Figure:
    """Build the interactive weekly pace forecast chart."""
    weekly, forecast = weekly_pace_forecast(splits_df)
    if weekly.empty:
        return go.Figure()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["pace_median"],
            mode="lines+markers",
            name="Actual pace",
        )
    )
    values = weekly["pace_median"].copy()
    if forecast is not None:
        forecast_week = weekly["week"].max() + pd.Timedelta(weeks=1)
        figure.add_trace(
            go.Scatter(
                x=[forecast_week],
                y=[forecast],
                mode="markers",
                marker={"symbol": "x", "size": 13},
                name="Forecast next week",
            )
        )
        values = pd.concat([values, pd.Series([forecast])], ignore_index=True)
    interactive_utils.apply_layout(figure, "Weekly median pace with forecast")
    figure.update_xaxes(title_text="Week")
    return interactive_utils.apply_pace_axis(figure, values)
