import sys
import requests
from datetime import datetime
import time
from refreshTokens import strava_tokens
import pandas
import databaseAccess

def setSplits(runId):
    splitsUrl = activitiesUrl + '/' + str(runId)
    print(f'Getting split information for [{runId}]')
    splitsRequest = requests.get(splitsUrl, headers=header).json()
    if 'message' in splitsRequest:
        # If we hit this, we've probably hit the rate limit so let's quit now
        print(splitsRequest)
        raise Exception("We've probably hit the rate limit, execute this again but with less pages")
    else:
	    # Otherwise, let's take a look at the splits
	    splitsDataSet = pandas.DataFrame(splitsRequest['splits_metric'])
	    splitsDataSet['id'] = runId
	    splitsDataSet['date'] = splitsRequest['start_date']
	    splitsDataSet['average_speed'] = splitsDataSet['average_speed']
	    splitsDataSet['average_grade_adjusted_speed'] = splitsDataSet['average_grade_adjusted_speed']
    return splitsDataSet

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
# Records per page
perPage = 50
# Set the activity index
index = 0
while True:
    try:
        header = {'Authorization': 'Bearer ' + access_token}
        param = {'per_page': perPage, 'page': page, 'after': start_date_unix}
        print(f'Checking for activites on page [{page}]')
        activityRequest = requests.get(activitiesUrl, headers=header, params=param).json()
        if (not activityRequest):
            print('No more activities found')
            break
        if 'message' in activityRequest:
            # If we hit this, we've probably hit the rate limit so let's quit now
            print(activityRequest)
            raise Exception("We've probably hit the rate limit")
            break
        for currentActivity in range(len(activityRequest)):
            runType = activityRequest[currentActivity]['type']
            if runType.lower() == "run":
                runId = activityRequest[currentActivity]['id']
                print(f'Found activity id {runId}, activity type {runType}')
                # Add columns that must exist
                activities.loc[index,'id'] = runId
                activities.loc[index,'name'] = activityRequest[currentActivity]['name']
                activities.loc[index,'upload_id'] = activityRequest[currentActivity]['upload_id']
                activities.loc[index,'type'] = activityRequest[currentActivity]['type']
                activities.loc[index,'start_date_local'] = activityRequest[currentActivity]['start_date_local']
                # Add columns that should exist
                if 'distance' in activityRequest[currentActivity]:
                    activities.loc[index,'distance'] = activityRequest[currentActivity]['distance']
                else:
                    activities.loc[index,'distance'] = 0
                if 'moving_time' in activityRequest[currentActivity]:
                    activities.loc[index,'moving_time'] = activityRequest[currentActivity]['moving_time']
                else:
                    activities.loc[index,'moving_time'] = 0
                if 'average_speed' in activityRequest[currentActivity]:
                    #pace = activityRequest[currentActivity]['average_speed']
                    #seconds = pace % 1
                    #pace = pace - seconds
                    #pace = round(pace)
                    #seconds = round(seconds * 60)
                    activities.loc[index,'average_speed'] = activityRequest[currentActivity]['average_speed']
                else:
                    activities.loc[index,'average_speed'] = 0
                if 'max_speed' in activityRequest[currentActivity]:
                    activities.loc[index,'max_speed'] = activityRequest[currentActivity]['max_speed']
                else:
                    activities.loc[index,'max_speed'] = 0
                if 'total_elevation_gain' in activityRequest[currentActivity]:
                    activities.loc[index,'total_elevation_gain'] = activityRequest[currentActivity]['total_elevation_gain']
                else:
                    activities.loc[index,'total_elevation_gain'] = 0
                if 'average_cadence' in activityRequest[currentActivity]:
                    activities.loc[index,'average_cadence'] = activityRequest[currentActivity]['average_cadence']
                else:
                    activities.loc[index,'average_cadence'] = 0
                index += 1
                splitsDataSet = setSplits(runId)
                # Add to split dataset
                splits = pandas.concat([splits, splitsDataSet])
        # Sleep, since we've now called the API twice we can give it a break for a second
        time.sleep(1)
        page += 1
    except:
        caughtException = sys.exc_info()[0]
        print(f'Caught an exception [{caughtException}], attempt to continue')
        break
# Insert everything we've collected
if not activities.empty:
    databaseAccess.setActvities(activities)
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
        databaseAccess.setSplits(splits)
# Do we have any activities inserted, where we're missing the splits?
activitiesMissingSplits = databaseAccess.getActvitiesMissingSplits()
missingSplits = pandas.DataFrame(columns = splitColumns)
for currentActivity in range(len(activitiesMissingSplits)):
    runId = activitiesMissingSplits.loc[currentActivity,'id']
    splitsDataSet = setSplits(runId)
if not splits.empty:
    # Only care about splits that are about 1k
    splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
    databaseAccess.setSplits(splits)