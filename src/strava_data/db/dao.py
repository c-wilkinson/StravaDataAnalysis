"""
Data Access Object (DAO) layer for reading/writing tokens and activity data.
Uses pyAesCrypt to decrypt/encrypt the SQLite database file, but only once at program start/end.
"""

import os
import sqlite3
from os import stat
from typing import Any, Dict, Optional

import pandas as pd
import pyAesCrypt

from strava_data.config import get_buffer_size, get_encryption_password
from utils.logger import get_logger

LOGGER = get_logger()

ENCRYPTED_DB_FILE = "strava.sqlite"
TEMP_DB_FILE = "strava_temp.sqlite"

CONFIG_TABLE = "config"
ACTIVITIES_TABLE = "activities"
SPLITS_TABLE = "splits"


def decrypt_database() -> None:
    """
    Decrypts strava.sqlite into strava_temp.sqlite (if strava.sqlite exists).
    If strava_temp.sqlite already exists, skip to avoid double-decryption.
    Call this once at program start.
    """
    if os.path.exists(TEMP_DB_FILE):
        LOGGER.warning("Database appears already decrypted. Skipping decryption.")
        return

    if not os.path.exists(ENCRYPTED_DB_FILE):
        LOGGER.warning(
            "Encrypted database file %s not found. Creating a new database.",
            ENCRYPTED_DB_FILE,
        )
        init_database()
        return

    enc_file_size = stat(ENCRYPTED_DB_FILE).st_size
    password = get_encryption_password()
    buffer_size = get_buffer_size()

    LOGGER.info("Decrypting database...")
    with open(ENCRYPTED_DB_FILE, "rb") as f_in, open(TEMP_DB_FILE, "wb") as f_out:
        pyAesCrypt.decryptStream(f_in, f_out, password, buffer_size, enc_file_size)

    LOGGER.info("Decryption complete. Working with the unencrypted file now.")


def encrypt_database() -> None:
    """
    Encrypts strava_temp.sqlite back into strava.sqlite and removes strava_temp.sqlite.
    Call this once at program end.
    """
    if not os.path.exists(TEMP_DB_FILE):
        LOGGER.warning("No decrypted DB file %s found to encrypt. Skipping.", TEMP_DB_FILE)
        return

    password = get_encryption_password()
    buffer_size = get_buffer_size()

    if os.path.exists(ENCRYPTED_DB_FILE):
        os.remove(ENCRYPTED_DB_FILE)

    LOGGER.info("Encrypting database back to strava.sqlite...")
    with open(TEMP_DB_FILE, "rb") as f_in, open(ENCRYPTED_DB_FILE, "wb") as f_out:
        pyAesCrypt.encryptStream(f_in, f_out, password, buffer_size)

    os.remove(TEMP_DB_FILE)
    LOGGER.info("Encryption complete.")


def init_database() -> None:
    """
    Creates required tables if they do not already exist in strava_temp.sqlite.
    Assumes decrypt_database() has already been called.
    """
    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {CONFIG_TABLE} (
            token_type TEXT,
            access_token TEXT,
            expires_at INTEGER,
            expires_in INTEGER,
            refresh_token TEXT
        );
    """
    )

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {ACTIVITIES_TABLE} (
            activity_id INTEGER PRIMARY KEY,
            name TEXT,
            activity_type TEXT,
            distance_m REAL,
            moving_time_s INTEGER,
            average_speed_m_s REAL,
            max_speed_m_s REAL,
            total_elevation_gain_m REAL,
            start_date_local TEXT,
            average_cadence REAL,
            is_outdoor INTEGER
        );
    """
    )

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SPLITS_TABLE} (
            split_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            distance_m REAL,
            elapsed_time_s INTEGER,
            elevation_difference_m REAL,
            moving_time_s INTEGER,
            pace_zone INTEGER,
            split_index INTEGER,
            average_grade_adjusted_speed_m_s REAL,
            average_heartrate REAL,
            start_date_local TEXT,
            FOREIGN KEY(activity_id) REFERENCES {ACTIVITIES_TABLE}(activity_id)
        );
    """
    )

    conn.commit()
    conn.close()


def store_tokens(tokens: Dict[str, Any]) -> None:
    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {CONFIG_TABLE};")
    cur.execute(
        f"""
        INSERT INTO {CONFIG_TABLE} (token_type, access_token, expires_at, expires_in, refresh_token)
        VALUES (?, ?, ?, ?, ?);
    """,
        (
            tokens.get("token_type"),
            tokens.get("access_token"),
            tokens.get("expires_at"),
            tokens.get("expires_in"),
            tokens.get("refresh_token"),
        ),
    )
    conn.commit()
    conn.close()


def read_tokens() -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT token_type, access_token, expires_at, expires_in, refresh_token
        FROM {CONFIG_TABLE}
        LIMIT 1;
    """
    )
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "token_type": row[0],
            "access_token": row[1],
            "expires_at": row[2],
            "expires_in": row[3],
            "refresh_token": row[4],
        }
    return None


def insert_activities(activities_df: pd.DataFrame) -> None:
    if activities_df.empty:
        return

    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()

    for _, row in activities_df.iterrows():
        cur.execute(
            f"""
            INSERT OR IGNORE INTO {ACTIVITIES_TABLE} (
                activity_id,
                name,
                activity_type,
                distance_m,
                moving_time_s,
                average_speed_m_s,
                max_speed_m_s,
                total_elevation_gain_m,
                start_date_local,
                average_cadence,
                is_outdoor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                row.get("id"),
                row.get("name"),
                row.get("type"),
                row.get("distance_m", 0.0),
                row.get("moving_time_s", 0),
                row.get("average_speed_m_s", 0.0),
                row.get("max_speed_m_s", 0.0),
                row.get("total_elevation_gain_m", 0.0),
                row.get("start_date_local", ""),
                row.get("average_cadence", 0.0),
                row.get("is_outdoor", 1 if row.get("is_outdoor") else 0),
            ),
        )
    conn.commit()
    conn.close()


def insert_splits(splits_df: pd.DataFrame) -> None:
    if splits_df.empty:
        return

    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()

    for _, row in splits_df.iterrows():
        cur.execute(
            f"""
            INSERT INTO {SPLITS_TABLE} (
                activity_id,
                distance_m,
                elapsed_time_s,
                elevation_difference_m,
                moving_time_s,
                pace_zone,
                split_index,
                average_grade_adjusted_speed_m_s,
                average_heartrate,
                start_date_local
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                row.get("activity_id"),
                row.get("distance_m", 0.0),
                row.get("elapsed_time_s", 0),
                row.get("elevation_difference_m", 0.0),
                row.get("moving_time_s", 0),
                row.get("pace_zone", 0),
                row.get("split_index", 0),
                row.get("average_grade_adjusted_speed_m_s", 0.0),
                row.get("average_heartrate", None),
                row.get("start_date_local", ""),
            ),
        )

    conn.commit()
    conn.close()


def get_latest_activity_date() -> Optional[str]:
    conn = sqlite3.connect(TEMP_DB_FILE)
    cur = conn.cursor()
    cur.execute(f"SELECT MAX(start_date_local) FROM {ACTIVITIES_TABLE};")
    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        return row[0]
    return None


def load_all_activities() -> pd.DataFrame:
    conn = sqlite3.connect(TEMP_DB_FILE)
    activities_df = pd.read_sql_query(f"SELECT * FROM {ACTIVITIES_TABLE};", conn)
    conn.close()
    return activities_df


def load_all_splits() -> pd.DataFrame:
    conn = sqlite3.connect(TEMP_DB_FILE)
    splits_df = pd.read_sql_query(f"SELECT * FROM {SPLITS_TABLE};", conn)
    conn.close()
    return splits_df
