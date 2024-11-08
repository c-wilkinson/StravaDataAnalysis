import requests
from datetime import datetime
import time
from refreshTokens import strava_tokens
import pandas
import databaseAccess

# Global variables
activityColumns = ['id', 'name', 'upload_id', 'type', 'distance', 'moving_time', 'average_speed', 'max_speed', 'total_elevation_gain', 'start_date_local', 'average_cadence']
splitColumns = ['average_speed', 'distance', 'elapsed_time', 'elevation_difference', 'moving_time', 'pace_zone', 'split', 'average_grade_adjusted_speed', 'average_heartrate', 'id', 'date']
activitiesUrl = "https://www.strava.com/api/v3/activities"
last_request_time = None
request_count = 0

# Rate limit variables
REQUESTS_PER_15_MINUTES = 100
REQUESTS_PER_24_HOURS = 1000
RATE_LIMIT_RESET_SECONDS = 60 * 15  # 15 minutes
RATE_LIMIT_RESET_24_HOURS = 60 * 60 * 24  # 24 hours
REQUEST_TIMEOUT = 10  # 10 seconds timeout for requests

def setSplits(runId, header):
    splitsUrl = activitiesUrl + '/' + str(runId)
    print(f'Getting split information for [{runId}]')
    try:
        splitsRequest = requests.get(splitsUrl, headers=header, timeout=REQUEST_TIMEOUT).json()
    except requests.exceptions.Timeout:
        print(f"Timeout occurred while fetching splits for run ID {runId}")
        return pandas.DataFrame()  # Return empty DataFrame if timeout
    if 'message' in splitsRequest:
        # If we hit this, we've probably hit the rate limit so let's quit now
        print(splitsRequest)
        raise Exception("We've probably hit the rate limit, execute this again but with fewer pages")
    # Otherwise, let's take a look at the splits
    splitsDataSet = pandas.DataFrame(splitsRequest['splits_metric'])
    splitsDataSet['id'] = runId
    splitsDataSet['date'] = splitsRequest['start_date']
    splitsDataSet['average_speed'] = splitsDataSet['average_speed']
    splitsDataSet['average_grade_adjusted_speed'] = splitsDataSet['average_grade_adjusted_speed']
    return splitsDataSet

def retrieveHeader():
    access_token = strava_tokens['access_token']
    # Set request header and parameters
    header = {'Authorization': 'Bearer ' + access_token}
    return header

def getStartData():
    start_date = databaseAccess.getLastDate()
    print(f'Get activities starting from [{start_date}]')
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
    start_date_tuple = start_date_dt.timetuple()
    start_date_unix = int(time.mktime(start_date_tuple))
    return start_date_unix

def make_api_request(url, headers, params=None):
    global last_request_time, request_count

    # Check rate limits
    if last_request_time:
        elapsed_time = time.time() - last_request_time
        if elapsed_time < RATE_LIMIT_RESET_SECONDS:
            if request_count >= REQUESTS_PER_15_MINUTES:
                wait_time = RATE_LIMIT_RESET_SECONDS - elapsed_time
                print(f'Rate limit reached. Waiting for {wait_time:.2f} seconds...')
                time.sleep(wait_time)
                # Reset rate limit variables
                last_request_time = None
                request_count = 0
    try:
        # Make API request
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        print("Timeout occurred while making API request")
        return None  # Return None if timeout occurs

    # Update rate limit variables
    last_request_time = time.time()
    request_count += 1

    # Check rate limits for 24 hours
    if request_count >= REQUESTS_PER_24_HOURS:
        wait_time = RATE_LIMIT_RESET_24_HOURS - elapsed_time
        print(f'Daily rate limit reached. Waiting for {wait_time:.2f} seconds...')
        time.sleep(wait_time)
        # Reset rate limit variables
        last_request_time = None
        request_count = 0

    return response

def getActivitiesAndSplits(header, start_date_unix, perPage=25, maxPages=2):
    # Create activities to append to
    activities = pandas.DataFrame(columns=activityColumns)
    # Create splits to append to
    splits = pandas.DataFrame(columns=splitColumns)
    page = 1
    index = 0
    while True:
        print(f'Checking for activities on page [{page}]')
        param = {'per_page': perPage, 'page': page, 'after': start_date_unix}
        activityRequest = make_api_request(activitiesUrl, header, params=param).json()
        if (not activityRequest):
            print('No more activities found')
            break
        if 'message' in activityRequest:
            # If we hit this, we've probably hit the rate limit so let's quit now
            print(activityRequest)
            raise Exception("We've probably hit the rate limit")
        for currentActivity, _ in enumerate(activityRequest):
            runType = activityRequest[currentActivity]['type']
            if runType.lower() == "run":
                runId = activityRequest[currentActivity]['id']
                print(f'Found activity id {runId}, activity type {runType}')
                # Add columns that must exist
                activities.loc[index, 'id'] = runId
                activities.loc[index, 'name'] = activityRequest[currentActivity]['name']
                activities.loc[index, 'upload_id'] = activityRequest[currentActivity]['upload_id']
                activities.loc[index, 'type'] = activityRequest[currentActivity]['type']
                activities.loc[index, 'start_date_local'] = activityRequest[currentActivity]['start_date_local']
                # Add columns that should exist
                if 'distance' in activityRequest[currentActivity]:
                    activities.loc[index, 'distance'] = activityRequest[currentActivity]['distance']
                else:
                    activities.loc[index, 'distance'] = 0
                if 'moving_time' in activityRequest[currentActivity]:
                    activities.loc[index, 'moving_time'] = activityRequest[currentActivity]['moving_time']
                else:
                    activities.loc[index, 'moving_time'] = 0
                if 'average_speed' in activityRequest[currentActivity]:
                    activities.loc[index, 'average_speed'] = activityRequest[currentActivity]['average_speed']
                else:
                    activities.loc[index, 'average_speed'] = 0
                if 'max_speed' in activityRequest[currentActivity]:
                    activities.loc[index, 'max_speed'] = activityRequest[currentActivity]['max_speed']
                else:
                    activities.loc[index, 'max_speed'] = 0
                if 'total_elevation_gain' in activityRequest[currentActivity]:
                    activities.loc[index, 'total_elevation_gain'] = activityRequest[currentActivity]['total_elevation_gain']
                else:
                    activities.loc[index, 'total_elevation_gain'] = 0
                if 'average_cadence' in activityRequest[currentActivity]:
                    activities.loc[index, 'average_cadence'] = activityRequest[currentActivity]['average_cadence']
                else:
                    activities.loc[index, 'average_cadence'] = 0
                index += 1
                splitsDataSet = setSplits(runId, header)
                # Add to split dataset
                splits = pandas.concat([splits, splitsDataSet])
        # Sleep, since we've now called the API twice we can give it a break for a second
        time.sleep(1)
        page += 1
        if (page > maxPages):
            print('Finished current max pages, try again in 15 minutes')
            break
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
    return activities, splits

if __name__ == '__main__':
    header = retrieveHeader()
    start_date_unix = getStartData()
    last_request_time = None
    request_count = 0
    # Retrieve rate limit info from the database
    rate_limit_info = databaseAccess.get_rate_limit_info()
    if rate_limit_info is None:
        # Handle the case when no rows are found
        last_request_time = time.time()
        request_count = 0
    else:
        # Unpack the values from the result tuple
        last_request_time, request_count = rate_limit_info
    activities, splits = getActivitiesAndSplits(header, start_date_unix)
    # Store the updated rate limit info in the database
    databaseAccess.update_rate_limit_info(last_request_time, request_count)
    # Insert everything we've collected
    if not activities.empty:
        databaseAccess.setActivities(activities)
        if not splits.empty:
            databaseAccess.setSplits(splits)
    # Do we have any activities inserted, where we're missing the splits?
    print('Checking for missing splits')
    activitiesMissingSplits = databaseAccess.getActivitiesMissingSplits()
    missingSplits = pandas.DataFrame(columns=splitColumns)
    for _, row in activitiesMissingSplits.iterrows():
        runId = row['id']
        splitsDataSet = setSplits(runId, header)
        # Add to split dataset
        splits = pandas.concat([splits, splitsDataSet])
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
        databaseAccess.setSplits(splits)
    # Delete activities that have no splits
    databaseAccess.deleteActivitiesMissingSplits()