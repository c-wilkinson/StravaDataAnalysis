"""
Client code to call Strava's API endpoints, with rate-limiting control.
"""

import time
from typing import Optional
from datetime import datetime

import requests
import pandas as pd

from strava_data.db.dao import read_tokens, insert_activities, get_latest_activity_date
from strava_data.strava_api.processing.transform import transform_activities
from utils.logger import get_logger

LOGGER = get_logger()

MAX_REQUESTS_15_MIN = 100
MAX_REQUESTS_DAY = 1000
RATE_LIMIT_15_MIN_SECONDS = 15 * 60
RATE_LIMIT_24_HOURS_SECONDS = 24 * 60 * 60


class RateLimiter:
    def __init__(self):
        self.last_request_time = None
        self.request_count = 0

    def update(self):
        self.last_request_time = time.time()
        self.request_count += 1

    def reset(self):
        self.last_request_time = None
        self.request_count = 0

    def should_wait(self) -> bool:
        if not self.last_request_time:
            return False
        elapsed = time.time() - self.last_request_time
        return elapsed < RATE_LIMIT_15_MIN_SECONDS and self.request_count >= MAX_REQUESTS_15_MIN

    def wait_if_needed(self):
        if self.should_wait():
            wait_time = RATE_LIMIT_15_MIN_SECONDS - (time.time() - self.last_request_time)
            LOGGER.warning("15-min rate limit reached. Waiting %f seconds.", wait_time)
            time.sleep(wait_time)
            self.reset()


rate_limiter = RateLimiter()


def fetch_activities(per_page: int = 30) -> pd.DataFrame:
    tokens = read_tokens()
    if not tokens:
        LOGGER.warning("No stored tokens. Returning empty DataFrame.")
        return pd.DataFrame()

    headers = {"Authorization": f"Bearer {tokens.get('access_token', '')}"}

    latest_str = get_latest_activity_date()
    if latest_str:
        latest_dt = datetime.strptime(latest_str, "%Y-%m-%dT%H:%M:%SZ")
        after_unix = int(latest_dt.timestamp())
        LOGGER.info("Fetching activities after %s (UNIX %d)", latest_str, after_unix)
    else:
        after_unix = 0
        LOGGER.info("No existing activities in DB, fetching all from start.")

    all_activities = pd.DataFrame()
    page = 1

    while True:
        LOGGER.info("Fetching page %d of activities", page)
        params = {"per_page": per_page, "page": page, "after": after_unix}
        response_data = _make_api_request(
            "https://www.strava.com/api/v3/athlete/activities", headers, params
        )

        if response_data is None:
            LOGGER.error("No data returned (None). Stopping fetch.")
            break

        if (
            isinstance(response_data, dict)
            and response_data.get("message") == "Rate Limit Exceeded"
        ):
            LOGGER.warning(
                "Strava rate limit exceeded. Waiting %d seconds.", RATE_LIMIT_15_MIN_SECONDS
            )
            time.sleep(RATE_LIMIT_15_MIN_SECONDS)
            rate_limiter.reset()
            continue

        if isinstance(response_data, list):
            page_df = pd.DataFrame(response_data)
            if page_df.empty:
                LOGGER.info("No more activities on page %d. Ending fetch.", page)
                break

            all_activities = pd.concat([all_activities, page_df], ignore_index=True)
            transformed_df = transform_activities(page_df)
            insert_activities(transformed_df)

            page += 1
        else:
            LOGGER.error("Unexpected response data type: %s", type(response_data))
            break

    LOGGER.info("Fetched a total of %d activities", len(all_activities))
    return all_activities


def fetch_splits_if_needed(activities_df: pd.DataFrame) -> pd.DataFrame:
    tokens = read_tokens()
    if not tokens:
        return pd.DataFrame()

    headers = {"Authorization": f"Bearer {tokens.get('access_token', '')}"}
    all_splits = pd.DataFrame()

    for _, row in activities_df.iterrows():
        if str(row.get("type", "")).lower() != "run":
            continue

        activity_id = row.get("id")
        if not activity_id:
            continue

        splits_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        splits_data = _make_api_request(splits_url, headers, None)

        if isinstance(splits_data, dict) and splits_data.get("message") == "Rate Limit Exceeded":
            LOGGER.warning(
                "Hit 429 fetching splits for activity %d. Waiting %d seconds, then retrying once.",
                activity_id,
                RATE_LIMIT_15_MIN_SECONDS,
            )
            time.sleep(RATE_LIMIT_15_MIN_SECONDS)
            rate_limiter.reset()
            continue

        if not splits_data or "splits_metric" not in splits_data:
            continue

        df_splits = pd.DataFrame(splits_data["splits_metric"])
        df_splits["activity_id"] = activity_id
        df_splits["start_date_local"] = splits_data.get("start_date_local", "")
        all_splits = pd.concat([all_splits, df_splits], ignore_index=True)

    return all_splits


def _make_api_request(url: str, headers: dict, params: Optional[dict]) -> Optional[list]:
    rate_limiter.wait_if_needed()

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.exceptions.Timeout:
        LOGGER.error("Timeout occurred while making API request to %s", url)
        return None

    if response.status_code == 429:
        LOGGER.error("HTTP 429: Rate Limit Exceeded by Strava")
        rate_limiter.reset()
        return {"message": "Rate Limit Exceeded"}

    if not response.ok:
        LOGGER.error(
            "Request failed. Status: %d, Response: %s",
            response.status_code,
            response.text,
        )
        return None

    rate_limiter.update()

    try:
        return response.json()
    except ValueError:
        LOGGER.error("Invalid JSON response from %s", url)
        return None


def get_latest_activity_unix_timestamp() -> int:
    latest_str = get_latest_activity_date()
    if not latest_str:
        return 0

    latest_dt = datetime.strptime(latest_str, "%Y-%m-%dT%H:%M:%SZ")
    return int(latest_dt.timestamp())
