import requests
import json
import time
import os
import sqlite3
import pyAesCrypt
import io
from os import stat

client_id = '{{ secrets.client_id }}'
client_secret = '{{ secrets.client_secret }}'

bufferSize = 64 * 1024
password = '{{ secrets.encryption_password }}'
encFileSize = stat('strava.sqlite').st_size
with open('strava.sqlite', 'rb') as fIn:
    with open('strava_temp.sqlite', 'wb') as fOut:
        pyAesCrypt.decryptStream(fIn, fOut, password, bufferSize, encFileSize)
conn = sqlite3.connect('strava_temp.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT * FROM config')
rows = cur.fetchall()
conn.commit()
conn.close()
strava_tokens = json.loads(json.dumps( [dict(ix) for ix in rows] ))[0]
if strava_tokens['expires_at'] < time.time():
    response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': client_id,
                                'client_secret': client_secret,
                                'grant_type': 'refresh_token',
                                'refresh_token': strava_tokens['refresh_token']
                                }
                    )
    new_strava_tokens = response.json()
    conn = sqlite3.connect('strava.sqlite')
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS config')
    cur.execute('CREATE TABLE config (token_type VARCHAR, access_token VARCHAR, expires_at BIGINT, expires_in INT, refresh_token VARCHAR)')
    cur.execute('INSERT INTO config (token_type, access_token, expires_at, expires_in, refresh_token) values (?, ?, ?, ?, ?)', (strava_tokens['token_type'], strava_tokens['access_token'], strava_tokens['expires_at'], strava_tokens['expires_in'], strava_tokens['refresh_token']))
    conn.commit()
    conn.close()
    # Use new Strava tokens from now
    strava_tokens = new_strava_tokens
if os.path.exists('strava.sqlite'):
    os.remove('strava.sqlite')
with open('strava_temp.sqlite', 'rb') as fIn:
    with open('strava.sqlite', 'wb') as fOut:
        pyAesCrypt.encryptStream(fIn, fOut, password, bufferSize)
if os.path.exists('strava_temp.sqlite'):
    os.remove('strava_temp.sqlite')