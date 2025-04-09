"""
Generates an updated README.md at the top-level of the repository.
"""

import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sqlite3

# Adjust these imports to match your code structure:
from strava_data.db.dao import TEMP_DB_FILE, ACTIVITIES_TABLE
from strava_data.db.dao import decrypt_database, encrypt_database

# Build a path to the README.md in the top-level directory
# (one level above this file's folder).
README_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # go up one directory from 'generate_readme.py'
    "README.md"
)


def generate_readme() -> None:
    """
    1. Decrypts the DB if needed.
    2. Fetches the last run from the activities table.
    3. Calculates how long ago it was.
    4. Rebuilds README.md in the top-level directory with embedded graphs.
    5. Encrypts DB again if desired.
    """
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

    if os.path.exists(README_PATH):
        os.remove(README_PATH)

    with open(README_PATH, "w", encoding="utf-8") as handle:
        handle.write("# StravaDataAnalysis\n")
        handle.write(
            "This repository extracts data from the Strava API, stores it locally (encrypted), "
            "and generates visualizations.\n\n"
        )
        handle.write("## Generated Content\n")
        handle.write(f"Last run was {time_string} ago!\n\n")
        handle.write(
            '![Running Pace vs Elevation Change](Running_Pace_vs_Elevation_Change.png?raw=true "Pace vs Elevation")\n\n'
        )
        handle.write(
            '![Time Taken per Distance](Time_Taken_Distance.png?raw=true "Time Taken per Distance")\n\n'
        )
        handle.write(
            '![Running Pace over Time](Running_Pace_over_Time.png?raw=true "Running Pace over Time")\n\n'
        )
        handle.write(
            '![Running Pace vs Total Distance](Running_Pace_vs_Total_Distance.png?raw=true "Pace vs Distance")\n\n'
        )
        handle.write(
            '![Number of Runs per Distance](Number_of_Runs_per_Distance.png?raw=true "Number of Runs per Distance")\n\n'
        )
        handle.write(
            '![Fastest 1k Pace over Time](Fastest_1k_Pace_over_Time.png?raw=true "Fastest 1k Pace over Time")\n\n'
        )
        handle.write(
            '![Total Distance Run each month by year](Total_Distance_Ran_by_Month.png?raw=true "Total Distance by Month")\n\n'
        )
        handle.write(
            '![Pace by Day of Week](Pace_by_Day.png?raw=true "Pace by Day of Week")\n\n'
        )
        handle.write(
            '![Activity Heatmap](Activity_Heatmap.png?raw=true "Activity Heat Map")\n\n'
        )
        handle.write(
            '![Cumulative Distance Run per year](Cumulative_Distance.png?raw=true "Cumulative Distance Run per year")\n\n'
        )

        # Additional disclaimers, instructions, etc.
        handle.write("## Instructions\n")
        handle.write(
            "To use this project, create a Strava application at https://www.strava.com/settings/api.\n"
            "Use `localhost` as your callback domain.\n\n"
            "Then, obtain your authorization code, set your CLIENT_ID, CLIENT_SECRET, etc.\n"
            "Run the scripts to fetch new activities and generate these graphs!\n"
        )

    encrypt_database()


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

    # Attempt to parse the timestamp. Adjust format if needed.
    try:
        return datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        # If stored in different format, you can handle or fallback
        return None


if __name__ == "__main__":
    generate_readme()
