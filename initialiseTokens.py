import requests
import json
import os
import sqlite3
import pyAesCrypt

copied_code = '[LONGCODEHERE]'
client_id = '{{ secrets.client_id }}'
client_secret = '{{ secrets.client_secret }}'
response = requests.post(
                    url = 'https://www.strava.com/oauth/token',
                    data = {
                            'client_id': client_id,
                            'client_secret': client_secret,
                            'code': copied_code,
                            'grant_type': 'authorization_code'
                            }
)

strava_tokens = response.json()
if 'message' in strava_tokens:
    print(strava_tokens)
else:
    conn = sqlite3.connect('strava.sqlite')
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS config')
    cur.execute('CREATE TABLE config (token_type VARCHAR, access_token VARCHAR, expires_at BIGINT, expires_in INT, refresh_token VARCHAR)')
    cur.execute('INSERT INTO config (token_type, access_token, expires_at, expires_in, refresh_token) values (?, ?, ?, ?, ?)', (strava_tokens['token_type'], strava_tokens['access_token'], strava_tokens['expires_at'], strava_tokens['expires_in'], strava_tokens['refresh_token']))
    conn.commit()
    conn.close()
    bufferSize = 64 * 1024
    password = 'rx<UMTLQA!OUoW:`}~Gq<n!]x`0DdK'
    with open('strava.sqlite', 'rb') as fIn:
        with open('stravadata.sqlite', 'wb') as fOut:
            pyAesCrypt.encryptStream(fIn, fOut, password, bufferSize)
    if os.path.exists('strava.sqlite'):
        os.remove('strava.sqlite')
        os.rename('stravadata.sqlite','strava.sqlite')