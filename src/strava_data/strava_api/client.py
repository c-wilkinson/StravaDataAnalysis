"""
Client code to call Strava's API endpoints, with rate-limiting control.
"""

import time
import requests
import pandas as pd
from typing import Optional
from datetime import datetime
from strava_data.db.dao import read_tokens, insert_activities, get_latest_activity_date
from strava_data.strava_api.processing.transform import transform_activities
from utils.logger import get_logger

LOGGER = get_logger()

MAX_REQUESTS_15_MIN = 100
MAX_REQUESTS_DAY = 1000
RATE_LIMIT_15_MIN_SECONDS = 15 * 60
RATE_LIMIT_24_HOURS_SECONDS = 24 * 60 * 60

LAST_REQUEST_TIME = None
REQUEST_COUNT = 0


def fetch_activities(per_page: int = 30) -> pd.DataFrame:
    """
    Fetches all available activities from Strava, page by page, until
    an empty page is returned (no more data).
    
    Continues partial data approach:
      - Insert each page into the DB so we don't lose anything if we
        hit a rate limit.
      - If a 429 is encountered, we can either wait or stop.

    :param per_page: Number of activities per page request.
    :return: DataFrame of all fetched activities.
    """
    tokens = read_tokens()
    if not tokens:
        LOGGER.warning("No stored tokens. Returning empty DataFrame.")
        return pd.DataFrame()

    headers = {"Authorization": f"Bearer {tokens.get('access_token', '')}"}
    
    latest_str = get_latest_activity_date()
    if latest_str:
        dt = datetime.strptime(latest_str, "%Y-%m-%dT%H:%M:%SZ")
        after_unix = int(dt.timestamp())
        LOGGER.info("Fetching activities after %s (UNIX %d)", latest_str, after_unix)
    else:
        after_unix = 0
        LOGGER.info("No existing activities in DB, fetching all from start.")
    
    all_activities = pd.DataFrame()
    page = 1

    while True:
        LOGGER.info("Fetching page %d of activities", page)
        params = {
            "per_page": per_page,
            "page": page,
            "after": after_unix
        }
        response_data = _make_api_request("https://www.strava.com/api/v3/athlete/activities", headers, params)

        if response_data is None:
            # Possibly a timeout or non-429 error
            LOGGER.error("No data returned (None). Stopping fetch.")
            break

        # Check if rate limit exceeded (429)
        if isinstance(response_data, dict) and response_data.get("message") == "Rate Limit Exceeded":
            LOGGER.warning("Strava rate limit exceeded. Waiting %d seconds.", RATE_LIMIT_15_MIN_SECONDS)
            time.sleep(RATE_LIMIT_15_MIN_SECONDS)
            LAST_REQUEST_TIME = None
            REQUEST_COUNT = 0

        # If we get a list of activities
        if isinstance(response_data, list):
            page_df = pd.DataFrame(response_data)
            # If empty => no more data
            if page_df.empty:
                LOGGER.info("No more activities on page %d. Ending fetch.", page)
                break

            # Merge with overall DataFrame
            all_activities = pd.concat([all_activities, page_df], ignore_index=True)

            # Transform & store partial data
            transformed_df = transform_activities(page_df)
            insert_activities(transformed_df)

            page += 1  # Move on to next page

        else:
            # If response_data isn't a list, log it and break
            LOGGER.error("Unexpected response data type: %s", type(response_data))
            break

    LOGGER.info("Fetched a total of %d activities", len(all_activities))
    return all_activities


def fetch_splits_if_needed(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetches 1 km splits for each run in the input DataFrame.
    Returns a DataFrame of all splits combined.

    :param activities_df: DataFrame of activities (with 'id', 'type').
    :return: DataFrame of combined splits.
    """
    tokens = read_tokens()
    if not tokens:
        return pd.DataFrame()

    headers = {"Authorization": f"Bearer {tokens.get('access_token', '')}"}
    all_splits = pd.DataFrame()

    for _, row in activities_df.iterrows():
        # Only proceed for actual runs
        if str(row.get("type", "")).lower() != "run":
            continue
        activity_id = row.get("id")
        if not activity_id:
            continue

        splits_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        
        splits_data = _make_api_request(splits_url, headers, None)
        if isinstance(splits_data, dict) and splits_data.get("message") == "Rate Limit Exceeded":
            # 2) If 429, wait once for 15 minutes, then retry
            LOGGER.warning("Hit 429 when fetching splits for activity %d. Waiting %d seconds, then retrying once.", activity_id, RATE_LIMIT_15_MIN_SECONDS)
            time.sleep(RATE_LIMIT_15_MIN_SECONDS)
            LAST_REQUEST_TIME = None
            REQUEST_COUNT = 0
            continue

        # If we still don't have valid data or 'splits_metric' is missing, skip
        if not splits_data or "splits_metric" not in splits_data:
            continue

        df_splits = pd.DataFrame(splits_data["splits_metric"])
        df_splits["activity_id"] = activity_id
        df_splits["start_date_local"] = splits_data.get("start_date_local", "")
        all_splits = pd.concat([all_splits, df_splits], ignore_index=True)

    return all_splits



def _make_api_request(url: str, headers: dict, params: Optional[dict]) -> Optional[list]:
    """
    Handles rate-limited GET requests to the Strava API.

    :param url: Endpoint URL.
    :param headers: Request headers (including Authorization).
    :param params: Query parameters.
    :return: JSON list or dict from the API, or None if error/timeout.
    """
    global LAST_REQUEST_TIME, REQUEST_COUNT

    if LAST_REQUEST_TIME:
        elapsed = time.time() - LAST_REQUEST_TIME
        if elapsed < RATE_LIMIT_15_MIN_SECONDS:
            if REQUEST_COUNT >= MAX_REQUESTS_15_MIN:
                wait_time = RATE_LIMIT_15_MIN_SECONDS - elapsed
                LOGGER.warning("15-min rate limit reached. Waiting %f seconds.", wait_time)
                time.sleep(wait_time)
                LAST_REQUEST_TIME = None
                REQUEST_COUNT = 0

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.exceptions.Timeout:
        LOGGER.error("Timeout occurred while making API request to %s", url)
        return None

    if response.status_code == 429:
        LOGGER.error("HTTP 429: Rate Limit Exceeded by Strava")
        LAST_REQUEST_TIME = None
        REQUEST_COUNT = 0
        return {"message": "Rate Limit Exceeded"}

    if not response.ok:
        LOGGER.error("Request failed. Status: %d, Response: %s", response.status_code, response.text)
        return None

    LAST_REQUEST_TIME = time.time()        
    REQUEST_COUNT += 1

    try:
        return response.json()
    except ValueError:
        LOGGER.error("Invalid JSON response from %s", url)
        return None



def get_latest_activity_unix_timestamp() -> int:
    """
    Reads the max start_date_local from the DB, parses it, and returns an integer UNIX timestamp.
    If no data, returns 0 (the epoch).
    """
    latest_str = get_latest_activity_date()
    if not latest_str:
        return 0  # no activities in DB, fetch all

    # Convert the string to datetime (assuming Strava uses format "%Y-%m-%dT%H:%M:%SZ")
    # If your DB stores a different format, adjust accordingly.
    dt = datetime.strptime(latest_str, "%Y-%m-%dT%H:%M:%SZ")
    return int(dt.timestamp())
