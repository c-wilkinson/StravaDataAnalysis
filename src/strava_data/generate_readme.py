"""
Generates an updated README.md at the top-level of the repository.
"""

import os
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

from strava_data.db.dao import TEMP_DB_FILE, ACTIVITIES_TABLE
from strava_data.db.dao import decrypt_database, encrypt_database
from utils.logger import get_logger

LOGGER = get_logger()

# Build a path to the README.md in the top-level directory
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "README.md")


def generate_readme() -> None:
    """
    1. Decrypts the DB if needed.
    2. Fetches the last run from the activities table.
    3. Calculates how long ago it was.
    4. Rebuilds README.md in the top-level directory with embedded graphs.
    5. Encrypts DB again if desired.
    """
    LOGGER.info("Start generate_readme.")
    decrypt_database()

    last_run_time = get_last_run_time()
    time_string = "No runs found!"
    if last_run_time is not None:
        delta = relativedelta(datetime.now(), last_run_time)
        time_string = (
            f"{delta.years} years, "
            f"{delta.months} months, "
            f"{delta.days} days, "
            f"{delta.hours} hours and "
            f"{delta.minutes} minutes"
        )

    encrypt_database()
    if os.path.exists(README_PATH):
        os.remove(README_PATH)

    readme_dir = os.path.dirname(README_PATH)

    with open(README_PATH, "w", encoding="utf-8") as handle:
        handle.write("# StravaDataAnalysis\n")
        handle.write(
            "This repository extracts data from the Strava API, stores it locally (encrypted), "
            "and generates visualizations.\n\n"
            "If other people start using this, I'll try and streamline this process as much as I "
            "can.\n\n"
            "[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)]"
            "(http://unlicense.org/)\n"
            "[![CodeFactor]("
            "https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis/badge)]"
            "(https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis)\n"
            "[![Codacy Badge]("
            "https://api.codacy.com/project/badge/Grade/9f08e367a5594645aa30c1e31c54dbb8)]"
            "(https://app.codacy.com/gh/c-wilkinson/StravaDataAnalysis?"
            "utm_source=github.com&utm_medium=referral"
            "&utm_content=c-wilkinson/StravaDataAnalysis&utm_campaign=Badge_Grade)\n"
            "[![GenerateStats](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/"
            "generate-stats.yml/badge.svg)]"
            "(https://github.com/c-wilkinson/StravaDataAnalysis/actions"
            "/workflows/generate-stats.yml)\n"
            "[![CodeQL](https://github.com/"
            "c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml/"
            "badge.svg)]"
            "(https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/"
            "codeql-analysis.yml)\n\n"
        )
        handle.write("## Generated Content\n")
        handle.write(f"Last run was {time_string} ago!\n\n")

        # Dynamically insert all PNG images
        image_files = sorted(f for f in os.listdir(readme_dir) if f.endswith(".png"))
        for image in image_files:
            title = image.replace("_", " ").replace(".png", "").title()
            LOGGER.info("Adding %s to readme.md", title)
            handle.write(f'![{title}]({image}?raw=true "{title}")\n\n')

        handle.write("## Instructions\n")
        handle.write(
            "As I'm sure is obvious, I'm teaching myself python as I go so the code "
            "quality is not "
            "likely to be great. Do with it as you wish.\n\n"
            "1. To use, create an Application on Strava. This can be done here: "
            "https://www.strava.com/settings/api\n\n"
            "Give it a name, a website and an 'Authorization Callback Domain'. The "
            "'Authorization Callback "
            "Domain' should be 'local host'.\n\n"
            "2. Copy and paste the following link into your browser, replacing {CLIENTIDHERE} "
            "with your numeric "
            "Client ID found on your Strava application settings page.\n\n"
            "> http://www.strava.com/oauth/authorize?client_id={CLIENTIDHERE}&"
            "response_type=code&redirect_uri="
            "http://localhost/exchange_token&approval_prompt=force&scope="
            "profile:read_all,activity:read_all\n\n"
            "Click authorise when you visit the above link\n\n"
            "3. You will go to a 404 not found page with a link that looks like this: -\n\n"
            "> http://localhost/exchange_token?state=&code={LONGCODEHERE}"
            "&scope=read,activity:read_all,"
            "profile:read_all\n\n"
            "Copy the code after '&code=' to save for step 4. You will also need your "
            "client ID and client secret "
            "found on your Strava application settings page.\n\n"
            "4. Run 'get_tokens.py'. This will create the initial tokens required for "
            "the script.\n\n"
            "Once this has been completed, you can run 'main.py' which uses the tokens "
            "to get the data points. "
            "If the access_token has expired, it will refresh its tokens automatically "
            "during run time."
        )


def get_last_run_time():
    """
    Retrieves the latest run timestamp from 'activities' in strava_temp.sqlite,
    returning a datetime object or None if no runs exist.
    """
    if not os.path.exists(TEMP_DB_FILE):
        return None

    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()

    query = f"SELECT MAX(start_date_local) FROM {ACTIVITIES_TABLE};"
    cur.execute(query)
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return None

    try:
        return datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


if __name__ == "__main__":
    generate_readme()
