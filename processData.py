import visualiseData
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
# Commenting out for now as we're not using the new version of this yet
# import dataPredication
import databaseAccess

# py -c 'import processData; processData.generateReadme()'
def generateReadme():
    visualiseData.produceTimeElevation()
    visualiseData.produceTimeDistance()
    visualiseData.produceActivtyHistogram()
    visualiseData.produceElapsedTimeDistance()
    visualiseData.produceTimePace()
    visualiseData.getFastestTimes()
    visualiseData.produceTimeDistanceMonthYear()
    visualiseData.producePaceBoxplotByDay()
    visualiseData.produceCumulativeDistance()
    visualiseData.produceActivityHeatmap()
    lastRun = databaseAccess.getLastRun()
    delta = relativedelta(datetime.now(), lastRun)
    if os.path.exists('README.md'):
        os.remove('README.md')
    with open('README.md', 'w') as handle:
        handle.write('# StravaDataAnalysis\n')
        handle.write("Simple data extract from the Strava API to generate some data points I'm interested in.  If other people start using this, I'll try and streamline this process as much as I can.\n\n")
        handle.write('[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)\n')
        handle.write('[![CodeFactor](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis/badge)](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis)\n')
        handle.write('[![Codacy Badge](https://app.codacy.com/project/badge/Grade/baba43376e964984a52a9a12f7209ace)](https://www.codacy.com/gh/c-wilkinson/StravaDataAnalysis/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=c-wilkinson/StravaDataAnalysis&amp;utm_campaign=Badge_Grade)')
        handle.write('[![GenerateStats](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml)')
        handle.write('[![CodeQL](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml)\n\n')
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
        handle.write('Last run was {0} years, {1} months, {2} days, {3} hours and {4} minutes ago!\n\n'.format(delta.years, delta.months, delta.days, delta.hours, delta.minutes))
        handle.write('![Running Pace vs Elevation Change](Running_Pace_vs_Elevation_Change.png?raw=true "Pace vs Elevation")\n\n')
        handle.write('![Time Taken per Distance](Time_Taken_Distance.png?raw=true "Time Taken per Distance")\n\n')
        handle.write('![Running Pace over Time](Running_Pace_over_Time.png?raw=true "Running Pace over Time")\n\n')
        handle.write('![Running Pace vs Total Distance on that run](Running_Pace_vs_Total_Distance.png?raw=true "Pace vs Distance")\n\n')
        handle.write('![Number of Runs per Distance](Number_of_Runs_per_Distance.png?raw=true "Pace vs Distance")\n\n')
        handle.write('![Fastest 1k Pace over Time](Fastest_1k_Pace_over_Time.png?raw=true "Running 1k Pace over Time")\n\n')
        handle.write('![Total Distance Run each month by year](Total_Distance_Ran_by_Month.png?raw=true "Total Distance Run each month by year")\n\n')
        handle.write('![Pace by day](Pace_by_Day.png?raw=true "Running Pace per day")\n\n')
        handle.write('![Activity Heatmap](Activity_Heatmap.png?raw=true "Activity Heat Map")\n\n')
        handle.write('![Cumulative Distance Run per year](Cumulative_Distance.png?raw=true "Cumulative Distance Run per year")\n')
        handle.write('![Weekly Distance Run per year](Weekly_Distance_Run_per_Year.png?raw=true "Weekly Distance Run per year")\n')

if __name__ == '__main__':
    generateReadme()
