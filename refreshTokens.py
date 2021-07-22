import requests
import time
import databaseAccess
import os

client_id = os.environ.get('CLIENTID')
client_secret = os.environ.get('CLIENTSECRET')
strava_tokens = databaseAccess.getConfig()
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
    databaseAccess.setConfig(strava_tokens)
    # Use new Strava tokens from now
    strava_tokens = new_strava_tokens