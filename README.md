# StravaDataAnalysis
This repository extracts data from the Strava API, stores it locally (encrypted), and generates visualizations.

If other people start using this, I'll try and streamline this process as much as I can.

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![CodeFactor](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis/badge)](https://www.codefactor.io/repository/github/c-wilkinson/stravadataanalysis)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9f08e367a5594645aa30c1e31c54dbb8)](https://app.codacy.com/gh/c-wilkinson/StravaDataAnalysis?utm_source=github.com&utm_medium=referral&utm_content=c-wilkinson/StravaDataAnalysis&utm_campaign=Badge_Grade)
[![CodeTest](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/test-code.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/test-code.yml)
[![GenerateStats](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/generate-stats.yml)
[![CodeQL](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/c-wilkinson/StravaDataAnalysis/actions/workflows/codeql-analysis.yml)

## Generated Content
📅 Stats last updated on: **2025-06-02 04:51:01**

🏃‍♂️ Most recent run: 0 years, 0 months, 6 days, 10 hours and 36 minutes

![A.I. Recommended Training](A.I._Recommended_Training.png?raw=true "A.I. Recommended Training")

![Activity Heatmap](Activity_Heatmap.png?raw=true "Activity Heatmap")

![Cadence Over Time](Cadence_Over_Time.png?raw=true "Cadence Over Time")

![Cumulative Distance](Cumulative_Distance.png?raw=true "Cumulative Distance")

![Elevation Gain Distribution](Elevation_Gain_Distribution.png?raw=true "Elevation Gain Distribution")

![Elevation Gain Per Km By Month](Elevation_Gain_per_KM_by_Month.png?raw=true "Elevation Gain Per Km By Month")

![Fastest 1K Pace Over Time](Fastest_1k_Pace_over_Time.png?raw=true "Fastest 1K Pace Over Time")

![Forecast Weekly Pace](Forecast_Weekly_Pace.png?raw=true "Forecast Weekly Pace")

![Longest Run Per Month](Longest_Run_per_Month.png?raw=true "Longest Run Per Month")

![Median 1K Pace Over Time](Median_1k_Pace_over_Time.png?raw=true "Median 1K Pace Over Time")

![Monthly Distance By Year](Monthly_Distance_by_Year.png?raw=true "Monthly Distance By Year")

![Number Of Runs Per Distance](Number_of_Runs_per_Distance.png?raw=true "Number Of Runs Per Distance")

![Pace Consistency By Run](Pace_Consistency_by_Run.png?raw=true "Pace Consistency By Run")

![Pace Distribution](Pace_Distribution.png?raw=true "Pace Distribution")

![Pace By Day](Pace_by_Day.png?raw=true "Pace By Day")

![Rest Days Heatmap](Rest_Days_Heatmap.png?raw=true "Rest Days Heatmap")

![Rolling 30 Day Comparison](Rolling_30_Day_Comparison.png?raw=true "Rolling 30 Day Comparison")

![Run Days Heatmap](Run_Days_Heatmap.png?raw=true "Run Days Heatmap")

![Run Distance Distribution](Run_Distance_Distribution.png?raw=true "Run Distance Distribution")

![Run Rest Ratio Heatmap](Run_Rest_Ratio_Heatmap.png?raw=true "Run Rest Ratio Heatmap")

![Run Start Time By Month](Run_Start_Time_by_Month.png?raw=true "Run Start Time By Month")

![Run Type Clusters](Run_Type_Clusters.png?raw=true "Run Type Clusters")

![Run Type Distribution By Year](Run_Type_Distribution_By_Year.png?raw=true "Run Type Distribution By Year")

![Running Pace Over Time](Running_Pace_over_Time.png?raw=true "Running Pace Over Time")

![Running Pace Vs Elevation Change](Running_Pace_vs_Elevation_Change.png?raw=true "Running Pace Vs Elevation Change")

![Running Pace Vs Total Distance](Running_Pace_vs_Total_Distance.png?raw=true "Running Pace Vs Total Distance")

![Time Taken Distance](Time_Taken_Distance.png?raw=true "Time Taken Distance")

![Total Distance Ran By Month](Total_Distance_Ran_by_Month.png?raw=true "Total Distance Ran By Month")

![Training Intensity By Heartrate Zone](Training_Intensity_by_HeartRate_Zone.png?raw=true "Training Intensity By Heartrate Zone")

![Training Load Over Time](Training_Load_Over_Time.png?raw=true "Training Load Over Time")

![Vo2 Proxy Over Time](VO2_Proxy_Over_Time.png?raw=true "Vo2 Proxy Over Time")

## Instructions
As I'm sure is obvious, I'm teaching myself python as I go so the code quality is not likely to be great. Do with it as you wish.

1. To use, create an Application on Strava. This can be done here: https://www.strava.com/settings/api

Give it a name, a website and an 'Authorization Callback Domain'. The 'Authorization Callback Domain' should be 'local host'.

2. Copy and paste the following link into your browser, replacing {CLIENTIDHERE} with your numeric Client ID found on your Strava application settings page.

> http://www.strava.com/oauth/authorize?client_id={CLIENTIDHERE}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all

Click authorise when you visit the above link

3. You will go to a 404 not found page with a link that looks like this: -

> http://localhost/exchange_token?state=&code={LONGCODEHERE}&scope=read,activity:read_all,profile:read_all

Copy the code after '&code=' to save for step 4. You will also need your client ID and client secret found on your Strava application settings page.

4. Run 'get_tokens.py'. This will create the initial tokens required for the script.

Once this has been completed, you can run 'main.py' which uses the tokens to get the data points. If the access_token has expired, it will refresh its tokens automatically during run time.