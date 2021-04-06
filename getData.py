import os
import requests
import json
from datetime import datetime
import time
from refreshTokens import strava_tokens
import pandas
import matplotlib
from matplotlib import pyplot
from matplotlib import dates
import numpy
import databaseAccess
calls = 0
page = 1
activitiesUrl = "https://www.strava.com/api/v3/activities"
access_token = strava_tokens['access_token']
start_date = databaseAccess.getLastDate()
print(f'Get activities starting from [{start_date}]')
start_date_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
start_date_tuple = start_date_dt.timetuple()
start_date_unix = int(time.mktime(start_date_tuple))
# Columns we're interested in
activityColumns = ['id', 'name', 'upload_id', 'type', 'distance', 'moving_time', 'average_speed', 'max_speed','total_elevation_gain', 'start_date_local', 'average_cadence']
splitColumns = ['average_speed', 'distance', 'elapsed_time', 'elevation_difference', 'moving_time', 'pace_zone', 'split', 'average_grade_adjusted_speed', 'average_heartrate', 'id', 'date']
# Create activities to append to
activities = pandas.DataFrame(columns = activityColumns)
# Create splits to append to
splits = pandas.DataFrame(columns = splitColumns)
while True:
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 50, 'page': page, 'after': start_date_unix}
    print(f'Checking for activites on page [{page}]')
    activityDataSet = requests.get(activitiesUrl, headers=header, params=param).json()
    calls += 1
    if (not activityDataSet):
        print('No more activities found')
        break
    if 'message' in activityDataSet:
        # If we hit this, we've probably hit the rate limit so let's quit now
        print(activityDataSet)
        break
    for currentActivity in range(len(activityDataSet)):
        type = activityDataSet[currentActivity]['type']
        if type.lower() == "run":
            runId = activityDataSet[currentActivity]['id']
            # Add columns that must exist
            activities.loc[currentActivity + (page-1)*200,'id'] = runId
            activities.loc[currentActivity + (page-1)*200,'name'] = activityDataSet[currentActivity]['name']
            activities.loc[currentActivity + (page-1)*200,'upload_id'] = activityDataSet[currentActivity]['upload_id']
            activities.loc[currentActivity + (page-1)*200,'type'] = activityDataSet[currentActivity]['type']
            activities.loc[currentActivity + (page-1)*200,'start_date_local'] = activityDataSet[currentActivity]['start_date_local']
            # Add columns that should exist
            if 'distance' in activityDataSet[currentActivity]:
                activities.loc[currentActivity + (page-1)*200,'distance'] = activityDataSet[currentActivity]['distance']
            if 'moving_time' in activityDataSet[currentActivity]:
                activities.loc[currentActivity + (page-1)*200,'moving_time'] = activityDataSet[currentActivity]['moving_time']
            if 'average_speed' in activityDataSet[currentActivity]:
                #pace = activityDataSet[currentActivity]['average_speed']
                #seconds = pace % 1
                #pace = pace - seconds
                #pace = round(pace)
                #seconds = round(seconds * 60)
                activities.loc[currentActivity + (page-1)*200,'average_speed'] = activityDataSet[currentActivity]['average_speed']
            if 'max_speed' in activityDataSet[currentActivity]:
                activities.loc[currentActivity + (page-1)*200,'max_speed'] = activityDataSet[currentActivity]['max_speed']
            if 'total_elevation_gain' in activityDataSet[currentActivity]:
                activities.loc[currentActivity + (page-1)*200,'total_elevation_gain'] = activityDataSet[currentActivity]['total_elevation_gain']
            if 'average_cadence' in activityDataSet[currentActivity]:
                activities.loc[currentActivity + (page-1)*200,'average_cadence'] = activityDataSet[currentActivity]['average_cadence']
            splitsUrl = activitiesUrl + '/' + str(runId)
            print(f'Getting split information for [{runId}]')
            splitsRequest = requests.get(splitsUrl, headers=header).json()
            calls += 1
            if 'message' in splitsRequest:
                # If we hit this, we've probably hit the rate limit so let's quit now
                print(splitsRequest)
                break
            # Otherwise, let's take a look at the splits
            splitsDataSet = pandas.DataFrame(splitsRequest['splits_metric']) 
            splitsDataSet['id'] = runId
            splitsDataSet['date'] = splitsRequest['start_date']
            splitsDataSet['average_speed'] = splitsDataSet['average_speed']
            splitsDataSet['average_grade_adjusted_speed'] = splitsDataSet['average_grade_adjusted_speed']
            # Add to split dataset
            splits = pandas.concat([splits, splitsDataSet])
    # Sleep, since we've now called the API twice we can give it a break for a second
    time.sleep(1)
    page += 1
    if calls > 50:
        print('Hit our limit of calls to the API this 15 minute interval, wait for 15 minutes to continue')
        break
if not activities.empty:
    databaseAccess.setActvities(activities)
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
        databaseAccess.setSplits(splits)
