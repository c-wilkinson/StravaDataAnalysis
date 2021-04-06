import requests
import json
from databaseAccess import setConfig

copied_code = '[LONGCODEHERE]'
client_id = '{{ secrets.CLIENTID }}'
client_secret = '{{ secrets.CLIENTSECRET }}'

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
    setConfig(strava_tokens)