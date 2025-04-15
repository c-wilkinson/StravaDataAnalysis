"""
Allows a one-time, manual retrieval of Strava tokens using an authorization code.
Usage:
  1. Run: python get_tokens.py
  2. Paste the authorization code when prompted.
  3. The script will request tokens from Strava and store them in the encrypted database.
"""

import requests

from strava_data.db.dao import decrypt_database, encrypt_database, store_tokens


def main() -> None:
    """
    Steps:
      1. Prompt user for the 'authorization code' from the redirect URL.
      2. Fetch tokens from Strava's /oauth/token endpoint.
      3. Store tokens in the DB (encrypting at the end).
    """
    print("=== Strava Token Retrieval ===")
    print(
        "After creating a Strava application and authorizing it, you obtain a code "
        "in the redirect URL."
    )
    print(
        "Example redirect URL: http://localhost/exchange_token?state=&code=LONGCODEHERE"
        "&scope=read,activity:read_all,profile:read_all"
    )
    print("Enter your LONGCODEHERE value below.\n")

    auth_code = input("Paste your Strava authorization code: ").strip()
    if not auth_code:
        print("No authorization code provided. Exiting.")
        return

    client_id = input("Paste your Strava client id: ").strip()
    if not client_id:
        print("No client id provided. Exiting.")
        return

    client_secret = input("Paste your Strava client secret: ").strip()
    if not client_secret:
        print("No client secret provided. Exiting.")
        return

    print("\nRequesting tokens from Strava...")
    try:
        response = requests.post(
            url="https://www.strava.com/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": auth_code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
    except requests.exceptions.Timeout:
        print("Timeout occurred while requesting Strava tokens.")
        return

    strava_tokens = response.json()
    if "errors" in strava_tokens or "message" in strava_tokens:
        print("Failed to retrieve tokens. Strava responded with:")
        print(strava_tokens)
        return

    print("Successfully retrieved tokens!")
    print(strava_tokens)

    print("\nStoring tokens in the database...")
    decrypt_database()
    store_tokens(strava_tokens)
    encrypt_database()
    print("Tokens stored successfully. Database re-encrypted.\n")


if __name__ == "__main__":
    main()
