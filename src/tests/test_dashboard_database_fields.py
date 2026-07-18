"""Tests for database fields required by the Parquet dashboard export."""

import sqlite3

from strava_data.db import dao


def test_init_database_migrates_existing_activity_table(tmp_path, monkeypatch):
    """An existing encrypted-database schema gains dashboard activity fields."""
    database_path = tmp_path / "strava_temp.sqlite"
    connection = sqlite3.connect(database_path)
    connection.execute(
        """
        CREATE TABLE activities (
            activity_id INTEGER PRIMARY KEY,
            name TEXT,
            activity_type TEXT,
            distance_m REAL,
            moving_time_s INTEGER,
            average_speed_m_s REAL,
            max_speed_m_s REAL,
            total_elevation_gain_m REAL,
            start_date_local TEXT,
            average_cadence REAL
        );
        """
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(dao, "TEMP_DB_FILE", str(database_path))

    dao.init_database()

    connection = sqlite3.connect(database_path)
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(activities);").fetchall()
    }
    connection.close()
    assert {"average_heartrate", "max_heartrate", "is_outdoor"}.issubset(columns)
