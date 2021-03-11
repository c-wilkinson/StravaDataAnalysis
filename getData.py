import requests
import json
import refreshTokens
from refreshTokens import strava_tokens

page = 1
url = "https://www.strava.com/api/v3/activities"
access_token = strava_tokens['access_token']

r = requests.get(url + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))
r = r.json()
print(r)