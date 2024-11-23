# StravaDataAnalysis
Simple data extract from the Strava API to generate some data points I'm interested in.  If other people start using this, I'll try and streamline this process as much as I can.

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![CodeFactor](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis/badge)](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9f08e367a5594645aa30c1e31c54dbb8)](https://app.codacy.com/gh/c-wilkinson/StravaDataAnalysis?utm_source=github.com&utm_medium=referral&utm_content=c-wilkinson/StravaDataAnalysis&utm_campaign=Badge_Grade)
[![GenerateStats](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml)
[![CodeQL](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml)

## Generated Content
Last run was 0 years, 0 months, 2 days, 20 hours and 59 minutes ago!

![Running Pace vs Elevation Change](Running_Pace_vs_Elevation_Change.png?raw=true "Pace vs Elevation")

![Time Taken per Distance](Time_Taken_Distance.png?raw=true "Time Taken per Distance")

![Running Pace over Time](Running_Pace_over_Time.png?raw=true "Running Pace over Time")

![Running Pace vs Total Distance on that run](Running_Pace_vs_Total_Distance.png?raw=true "Pace vs Distance")

![Number of Runs per Distance](Number_of_Runs_per_Distance.png?raw=true "Pace vs Distance")

![Fastest 1k Pace over Time](Fastest_1k_Pace_over_Time.png?raw=true "Running 1k Pace over Time")

![Total Distance Run each month by year](Total_Distance_Ran_by_Month.png?raw=true "Total Distance Run each month by year")

![Pace by day](Pace_by_Day.png?raw=true "Running Pace per day")

![Activity Heatmap](Activity_Heatmap.png?raw=true "Activity Heat Map")

![Cumulative Distance Run per year](Cumulative_Distance.png?raw=true "Cumulative Distance Run per year")

![Weekly Distance Run per year](Weekly_Distance_Run_per_Year.png?raw=true "Weekly Distance Run per year")

![VO₂ Max Over Time](VO2_Max_Over_Time.png?raw=true "VO₂ Max Over Time")

![Monthly Consistency Analysis](Monthly_Consistency_Analysis.png?raw=true "Monthly Consistency Analysis")

## Instructions
As I'm sure is obvious, I'm teaching myself python as I go so the code quality is not likely to be great.  Do with it as you wish.

1.To use, create an Application on Strava.  This can be done here: https://www.strava.com/settings/api
Give it a name, a website and an "Authorization Callback Domain".  The "Authorization Callback Domain" should be "local host".

2.Copy and paste the following link into your browser, replacing {CLIENTIDHERE} with your numeric Client ID found on your Strava application settings page.
> http://www.strava.com/oauth/authorize?client_id={CLIENTIDHERE}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all

Click authorise when you visit the above link

3.You will go to a 404 not found page with a link that looks like this: -
> http://localhost/exchange_token?state=&code={LONGCODEHERE}&scope=read,activity:read_all,profile:read_all

Copy the code after "&code=" to save for step 4.

4.Open "getTokens.py", paste your code from step 3 to the variable "copied_code".  Add the client_id from your Application on Strava to the client_id variable.  Add the client_secret from your Application on Strava to the client_secret variable.  Save the changes.

5.Run "getTokens.py".  This will create the initial tokens required for the script.

6.Open "refreshTokens.py", add the client_id from your Application on Strava to the client_id variable.  Add the client_secret from your Application on Strava to the client_secret variable.  Save the changes.

Once this has been completed, you can run "getData.py" which uses the tokens to get the data points.  If the access_token has expired, it will use the refresh_token to get a new token.

