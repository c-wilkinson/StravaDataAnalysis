import sys
import requests
from datetime import datetime
import time
from refreshTokens import strava_tokens
import pandas
import databaseAccess
import visualiseData
import dataPredication
import os

# Global variables
activityColumns = ['id', 'name', 'upload_id', 'type', 'distance', 'moving_time', 'average_speed', 'max_speed','total_elevation_gain', 'start_date_local', 'average_cadence']
splitColumns = ['average_speed', 'distance', 'elapsed_time', 'elevation_difference', 'moving_time', 'pace_zone', 'split', 'average_grade_adjusted_speed', 'average_heartrate', 'id', 'date']
activitiesUrl = "https://www.strava.com/api/v3/activities"

def setSplits(runId, header):
    splitsUrl = activitiesUrl + '/' + str(runId)
    print(f'Getting split information for [{runId}]')
    splitsRequest = requests.get(splitsUrl, headers=header).json()
    if 'message' in splitsRequest:
        # If we hit this, we've probably hit the rate limit so let's quit now
        print(splitsRequest)
        raise Exception("We've probably hit the rate limit, execute this again but with less pages")
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

def getActivitesAndSplits(header, start_date_unix, perPage = 50):
    # Create activities to append to
    activities = pandas.DataFrame(columns = activityColumns)
    # Create splits to append to
    splits = pandas.DataFrame(columns = splitColumns)
    page = 1
    index = 0
    while True:
        try:
            print(f'Checking for activites on page [{page}]')
            param = {'per_page': perPage, 'page': page, 'after': start_date_unix}
            activityRequest = requests.get(activitiesUrl, headers=header, params=param).json()
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
                    splitsDataSet = setSplits(runId, header)
                    # Add to split dataset
                    splits = pandas.concat([splits, splitsDataSet])
            # Sleep, since we've now called the API twice we can give it a break for a second
            time.sleep(1)
            page += 1
        except:
            caughtException = sys.exc_info()[0]
            print(f'Caught an exception [{caughtException}], attempt to continue')
            break
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
    return activities, splits

def generateReadme():
    visualiseData.produceTimeElevation()
    visualiseData.produceTimeDistance()
    visualiseData.produceActivtyHistogram()
    if os.path.exists('README.md'):
        os.remove('README.md')
    with open('README.md', 'w') as handle:
        handle.write('# StravaDataAnalysis\n')
        handle.write("Simple data extract from the Strava API to generate some data points I'm interested in.  If other people start using this, I'll try and streamline this process as much as I can.\n\n")
        handle.write('[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)\n')
        handle.write('[![CodeFactor](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis/badge)](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis)\n')
        handle.write('[![Codacy Badge](https://app.codacy.com/project/badge/Grade/baba43376e964984a52a9a12f7209ace)](https://www.codacy.com/gh/c-wilkinson/StravaDataAnalysis/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=c-wilkinson/StravaDataAnalysis&amp;utm_campaign=Badge_Grade)\n\n')
        handle.write("As I'm sure is obvious, I'm teaching myself python as I go so the code quality is not likely to be great.  Do with it as you wish.\n\n")
        handle.write('1.To use, create an Application on Strava.  This can be done here: https://www.strava.com/settings/api\n')
        handle.write('Give it a name, a website and an "Authorization Callback Domain".  The "Authorization Callback Domain" should be "local host".\n\n')
        handle.write('2.Copy and paste the following link into your browser, replacing {CLIENTIDHERE} with your numeric Client ID found on your Strava application settings page.\n')
        handle.write('> http://www.strava.com/oauth/authorize?client_id={CLIENTIDHERE}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all\n\n')
        handle.write('Click authorise when you visit the above link\n\n')
        handle.write('3.You will go to a 404 not found page with a link that looks like this: -\n')
        handle.write('> http://localhost/exchange_token?state=&code={LONGCODEHERE}&scope=read,activity:read_all,profile:read_all\n\n')
        handle.write('Copy the code after "&code=" to save for step 4.\n\n')
        handle.write('4.Open "getTokens.py", paste your code from step 3 to the variable "copied_code".  Add the client_id from your Application on Strava to the client_id variable.  Add the client_secret from your Application on Strava to the client_secret variable.  Save the changes.\n\n')
        handle.write('5.Run "getTokens.py".  This will create the initial tokens required for the script.\n\n')
        handle.write('6.Open "refreshTokens.py", add the client_id from your Application on Strava to the client_id variable.  Add the client_secret from your Application on Strava to the client_secret variable.  Save the changes.\n\n')
        handle.write('Once this has been completed, you can run "getData.py" which uses the tokens to get the data points.  If the access_token has expired, it will use the refresh_token to get a new token.\n\n')
        handle.write('## Generated Content\n')
        handle.write('![Running Pace vs Elevation Change](Running_Pace_vs_Elevation_Change.png?raw=true "Pace vs Elevation")\n\n')
        handle.write('![Running Pace vs Total Distance on that run](Running_Pace_vs_Total_Distance.png?raw=true "Pace vs Distance")\n\n')
        handle.write('![Number of Runs per Distance](Number_of_Runs_per_Distance.png?raw=true "Pace vs Distance")\n\n')
        handle.write('### Predicating Race Times\n')
        handle.write("This uses the runs you've done in the past and scales to different race distances.  It assumes the race is flat and doesn't takes into account fatigue or weather or surface (lots of stuff. . . it's a bit of fun).\n")
        coeff = dataPredication.getCoefficientArray()
        handle.write('#### Predicated Race times based on all runs\n')
        handle.write(f'Best 5k predicated time: {dataPredication.predicateRun(5, coeff)}\n\n')
        handle.write(f'Best 10k predicated time: {dataPredication.predicateRun(10, coeff)}\n\n')
        handle.write(f'Best Half Marathon predicated time: {dataPredication.predicateRun(21.0975, coeff)}\n\n')
        handle.write(f'Best Marathon predicated time: {dataPredication.predicateRun(42.195, coeff)}\n\n')
        coeff = dataPredication.getCoefficientArray(3)
        handle.write('#### Predicated Race times based on last 3 months\n')
        handle.write(f'Best 5k predicated time: {dataPredication.predicateRun(5, coeff)}\n\n')
        handle.write(f'Best 10k predicated time: {dataPredication.predicateRun(10, coeff)}\n\n')
        handle.write(f'Best Half Marathon predicated time: {dataPredication.predicateRun(21.0975, coeff)}\n\n')
        handle.write(f'Best Marathon predicated time: {dataPredication.predicateRun(42.195, coeff)}\n')

if __name__ == '__main__':
    header = retrieveHeader()
    start_date_unix = getStartData()
    activities, splits = getActivitesAndSplits(header, start_date_unix)
    # Insert everything we've collected
    if not activities.empty:
        databaseAccess.setActvities(activities)
        if not splits.empty:
            databaseAccess.setSplits(splits)
    # Do we have any activities inserted, where we're missing the splits?
    print('Checking for missing splits')
    activitiesMissingSplits = databaseAccess.getActvitiesMissingSplits()
    missingSplits = pandas.DataFrame(columns = splitColumns)
    for _, row in activitiesMissingSplits.iterrows():
        runId = row['id']
        splitsDataSet = setSplits(runId, header)
        # Add to split dataset
        splits = pandas.concat([splits, splitsDataSet])
    if not splits.empty:
        # Only care about splits that are about 1k
        splits = splits[(splits.distance > 950) & (splits.distance < 1050)]
        databaseAccess.setSplits(splits)
    generateReadme()