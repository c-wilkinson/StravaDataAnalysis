"""
Handles Strava OAuth token retrieval and refresh logic.
"""

import json
import time
import requests
from strava_data.config import get_client_id, get_client_secret
from strava_data.db.dao import read_tokens, store_tokens
from utils.logger import get_logger

LOGGER = get_logger()


def get_or_refresh_tokens() -> None:
    """
    Reads existing tokens from the database.
    If expired, refreshes them via Strava OAuth.
    If none exist, the user must initially obtain them with a manual OAuth flow.
    """
    tokens = read_tokens()
    if not tokens:
        LOGGER.info("No tokens found in the database. Please obtain them initially.")
        return

    expires_at = tokens.get("expires_at", 0)
    if expires_at < time.time():
        LOGGER.info("Tokens expired. Refreshing now.")
        refresh_token = tokens.get("refresh_token", "")
        new_tokens = refresh_strava_tokens(refresh_token)
        if not new_tokens:
            raise RuntimeError("Token refresh failed")
        store_tokens(new_tokens)
    else:
        LOGGER.info("Tokens are still valid.")


def refresh_strava_tokens(refresh_token: str) -> dict:
    """
    Calls Strava's /oauth/token endpoint to refresh an expired token.

    :param refresh_token: The user's current refresh token from the DB.
    :return: Dictionary of new tokens, or an empty dict if refresh fails.
    """
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    payload_str = json.dumps(payload)
    LOGGER.info(payload_str)
    try:
        response = requests.post(url, data=payload, timeout=10)
    except requests.exceptions.Timeout:
        LOGGER.info("Token refresh request timed out.")
        return {}

    if response.ok:
        return response.json()

    LOGGER.info(
        "Failed to refresh tokens. Status: %s Response: %s", response.status_code, response.text
    )
    return {}
