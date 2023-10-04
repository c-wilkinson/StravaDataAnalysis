import requests
from datetime import datetime
import time
from refreshTokens import strava_tokens
import pandas
import databaseAccess

# Global variables
activityColumns = ['id', 'name', 'upload_id', 'type', 'distance', 'moving_time', 'average_speed', 'max_speed','total_elevation_gain', 'start_date_local', 'average_cadence']
splitColumns = ['average_speed', 'distance', 'elapsed_time', 'elevation_difference', 'moving_time', 'pace_zone', 'split', 'average_grade_adjusted_speed', 'average_heartrate', 'id', 'date']
activitiesUrl = "https://www.strava.com/api/v3/activities"

# Rate limit variables
REQUESTS_PER_15_MINUTES = 100
REQUESTS_PER_24_HOURS = 1000
RATE_LIMIT_RESET_SECONDS = 60 * 15  # 15 minutes
RATE_LIMIT_RESET_24_HOURS = 60 * 60 * 24  # 24 hours

def setSplits(runId, header):
    splitsUrl = activitiesUrl + '/' + str(runId)
    print(f'Getting split information for [{runId}]')
    splitsRequest = requests.get(splitsUrl, headers=header).json()
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

    # Make API request
    response = requests.get(url, headers=headers, params=params)

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

def getActivitesAndSplits(header, start_date_unix, per_page=25, max_pages=2):
    def fetchActivitesAndSplits(page):
        print(f'Checking for activities on page [{page}]')
        params = {'per_page': per_page, 'page': page, 'after': start_date_unix}
        activity_request = make_api_request(activitiesUrl, header, params=params).json()

        if not activity_request:
            print('No more activities found')
            return None, None

        if 'message' in activity_request:
            print(activity_request)
            raise Exception("Rate limit exceeded.")

        activities = []
        splits = []

        for activity in activity_request:
            run_type = activity['type'].lower()
            if run_type == "run":
                run_id = activity['id']
                print(f'Found activity id {run_id}, activity type {run_type}')
                activities.append({
                    'id': run_id,
                    'name': activity['name'],
                    'upload_id': activity['upload_id'],
                    'type': activity['type'],
                    'start_date_local': activity['start_date_local'],
                    'distance': activity.get('distance', 0),
                    'moving_time': activity.get('moving_time', 0),
                    'average_speed': activity.get('average_speed', 0),
                    'max_speed': activity.get('max_speed', 0),
                    'total_elevation_gain': activity.get('total_elevation_gain', 0),
                    'average_cadence': activity.get('average_cadence', 0)
                })
                splits_data_set = set_splits(run_id, header)
                splits.append(splits_data_set)

        return activities, splits

    activities = []
    splits = []

    for page in range(1, max_pages + 1):
        page_activities, page_splits = fetchActivitesAndSplits(page)
        if page_activities is None:
            break
        activities.extend(page_activities)
        if page_splits:
            splits.extend(page_splits)

    if splits:
        splits = pd.concat(splits)
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]

    return pd.DataFrame(activities), splits

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