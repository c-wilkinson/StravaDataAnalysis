import json
import os
import sqlite3
import pyAesCrypt
from os import stat

# Global variables for use by this file
bufferSize = {{ secrets.BUFFERSIZE }}
password = '{{ secrets.ENCRYPTIONPASSWORD }}'

def resetActivities():
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS activities;')
    conn.commit()
    conn.close()
    encryptDatabase()

def resetSplits():
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS splits;')
    conn.commit()
    conn.close()
    encryptDatabase()

def getLastDate():
    decryptDatabase()
    lastActivityDate = '1970-01-01T00:00:00Z'
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities';")
    result = cur.fetchone()
    if result is None:
        # There is data, so let's grab the max datetime
        cur.execute("SELECT MAX(start_date_local) FROM activities;")
        result = cur.fetchone()
        if result is None:
            # Found a max date
            lastActivityDate, = result
    conn.commit()
    conn.close()
    encryptDatabase()
    return lastActivityDate

def setConfig(strava_tokens):
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS config;')
    cur.execute('CREATE TABLE config (token_type VARCHAR, access_token VARCHAR, expires_at BIGINT, expires_in INT, refresh_token VARCHAR);')
    cur.execute('INSERT INTO config (token_type, access_token, expires_at, expires_in, refresh_token) values (?, ?, ?, ?, ?);', (strava_tokens['token_type'], strava_tokens['access_token'], strava_tokens['expires_at'], strava_tokens['expires_in'], strava_tokens['refresh_token']))
    conn.commit()
    conn.close()
    encryptDatabase()

def getConfig():
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM config')
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    encryptDatabase()
    return json.loads(json.dumps( [dict(ix) for ix in rows] ))[0]

# Must be called to access the database, otherwise it can't be read
def decryptDatabase():
    if os.path.exists('strava_temp.sqlite'):
        print('Database already decrypted!  Skipping. . .')
    else:
        if os.path.exists('strava.sqlite'):
            encFileSize = stat('strava.sqlite').st_size
            with open('strava.sqlite', 'rb') as fIn:
                with open('strava_temp.sqlite', 'wb') as fOut:
                    pyAesCrypt.decryptStream(fIn, fOut, password, bufferSize, encFileSize)
        else:
            print('Unable to find database to decrypt!  Skipping. . .')

# Always call this after you touch the database to re-encrypt it
def encryptDatabase():
    if os.path.exists('strava_temp.sqlite'):
        if os.path.exists('strava.sqlite'):
            os.remove('strava.sqlite')
        with open('strava_temp.sqlite', 'rb') as fIn:
            with open('strava.sqlite', 'wb') as fOut:
                pyAesCrypt.encryptStream(fIn, fOut, password, bufferSize)
        if os.path.exists('strava_temp.sqlite'):
            os.remove('strava_temp.sqlite')
    else:
        print('Unable to find database to encrypt, skipping...')
        
def setActvities(activities):
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS activities (id BIGINT, name NVARCHAR, upload_id BIGINT, type VARCHAR, distance NUMERIC, moving_time INT, average_speed NUMERIC, max_speed NUMERIC, total_elevation_gain NUMERIC, start_date_local DATETIME, average_cadence NUMERIC, UNIQUE(id));')
    conn.commit()
    for currentActivity in range(len(activities)):
        cur.execute('INSERT OR IGNORE INTO activities (id, name, upload_id, type, distance, moving_time, average_speed, max_speed, total_elevation_gain, start_date_local, average_cadence) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', (activities.loc[currentActivity,'id'], activities.loc[currentActivity,'name'], activities.loc[currentActivity,'upload_id'], activities.loc[currentActivity,'type'], activities.loc[currentActivity,'distance'], activities.loc[currentActivity,'moving_time'], activities.loc[currentActivity,'average_speed'], activities.loc[currentActivity,'max_speed'], activities.loc[currentActivity,'total_elevation_gain'], activities.loc[currentActivity,'start_date_local'], activities.loc[currentActivity,'average_cadence']))
        conn.commit()
    conn.close()
    encryptDatabase()

def setSplits(splits):
    decryptDatabase()
    conn = sqlite3.connect('strava_temp.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS splits (split_id INT, activity_id BIGINT, activity_date DATETIME, average_speed NUMERIC, distance NUMERIC, elapsed_time INT, elevation_difference NUMERIC, moving_time INT, pace_zone INT, split INT, average_grade_adjusted_speed NUMERIC, average_heartrate NUMERIC, UNIQUE(split_id, activity_id));')
    conn.commit()
    for currentSplit in range(len(splits)):
        cur.execute('INSERT OR IGNORE INTO splits (split_id, activity_id, activity_date, average_speed, distance, elapsed_time, elevation_difference, moving_time, pace_zone, split, average_grade_adjusted_speed, average_heartrate) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', (currentSplit, splits.loc[currentSplit,'id'], splits.loc[currentSplit,'date'], splits.loc[currentSplit,'average_speed'], splits.loc[currentSplit,'distance'], splits.loc[currentSplit,'elapsed_time'], splits.loc[currentSplit,'elevation_difference'], splits.loc[currentSplit,'moving_time'], splits.loc[currentSplit,'pace_zone'], splits.loc[currentSplit,'split'], splits.loc[currentSplit,'average_grade_adjusted_speed'], splits.loc[currentSplit,'average_heartrate']))
        conn.commit()
    conn.close()
    encryptDatabase()