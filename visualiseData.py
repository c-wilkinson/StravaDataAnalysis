import pandas
import dateutil
import datetime
import calendar
import seaborn
import matplotlib
import matplotlib.pylab
import numpy
import databaseAccess

# py -c 'import visualiseData; visualiseData.getFastestTimes()'
def getFastestTimes():
    splits = databaseAccess.getSplits()
    activities = splits[['activity_date', 'distance', 'elapsed_time']]
    produceFastest1k(activities)
    months=[]
    max_date = datetime.datetime.strptime((datetime.datetime.strptime(splits['activity_date'].max(),"%Y-%m-%dT%H:%M:%SZ")).strftime('%Y%m'),'%Y%m')
    min_date = datetime.datetime.strptime((datetime.datetime.strptime(splits['activity_date'].min(),"%Y-%m-%dT%H:%M:%SZ")).strftime('%Y%m'),'%Y%m')
    months.append(min_date)
    while min_date <= max_date:
        min_date = min_date + dateutil.relativedelta.relativedelta(months=1)
        months.append(min_date)

def produceFastest1k(activities):
    pandas.options.mode.chained_assignment = None
    activities['activity_date'] = [datetime.datetime.strptime((datetime.datetime.strptime(x,"%Y-%m-%dT%H:%M:%SZ")).strftime('%Y%m'),'%Y%m') for x in activities['activity_date']]
    activities['distance'] = activities['distance'].astype(float)
    activities['elapsed_time'] = activities['elapsed_time'].astype(float)
    activities.set_index(['activity_date'], inplace=True)
    fastestSplits = activities['elapsed_time'].groupby('activity_date').agg(elapsed_time=('min')).reset_index()
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in fastestSplits['elapsed_time']]
    dates = fastestSplits['activity_date']
    x = matplotlib.dates.date2num(dates)
    y = matplotlib.dates.date2num(times)
    matplotlib.pylab.plot_date(x, y, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    matplotlib.pyplot.title('Fastest 1k Pace over Time', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16, rotation='vertical')
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Month', fontsize=18)
    matplotlib.pyplot.ylabel('Pace (km / hh:mm:ss)', fontsize=18)
    seaborn.regplot(x = x, y = y, scatter=None, data = fastestSplits ,order = 2)
    loc= matplotlib.dates.AutoDateLocator()
    matplotlib.pyplot.gca().xaxis.set_major_locator(loc)
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gca().xaxis.set_major_formatter(matplotlib.dates.AutoDateFormatter(loc))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Fastest_1k_Pace_over_Time.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceTimeElevation()'
def produceTimeElevation():
    splits = databaseAccess.getSplits()
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time']]
    y = matplotlib.dates.date2num(times)
    matplotlib.pyplot.plot( splits['elevation_difference'], y, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = splits['elevation_difference'], y = y, scatter=None, order = 2)
    matplotlib.pyplot.title('Running Pace vs. Elevation Change', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Elevation Change (m)', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (hh:mm:ss)', fontsize=18)
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Running_Pace_vs_Elevation_Change.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceTimeDistanceYear()'
def produceTimeDistanceYear():
    splits = databaseAccess.getSplits()
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time']]
    years = [dateutil.parser.parse(date).year for date in splits['start_date_local']]
    unique_years = sorted(set(years))
    cmap = matplotlib.pyplot.cm.get_cmap('tab10')
    num_colors = len(unique_years)
    colors = cmap.colors[:num_colors] 
    matplotlib.pyplot.figure(figsize=(10, 6))
    for year, color in zip(unique_years, colors):
        indices = [i for i, y in enumerate(years) if y == year]
        distance = [splits['total_distance'][i] for i in indices]
        pace = [times[i] for i in indices]       
        matplotlib.pyplot.plot(distance, pace, linestyle='', marker='o', markersize=5, alpha=0.3, color=color, label=str(year))
        seaborn.regplot(x=distance, y=pace, scatter=None, order=2, color=color)
    matplotlib.pyplot.title('Running Pace vs. Total Distance', fontsize=18, fontweight='bold')
    matplotlib.pyplot.xticks(fontsize=12)
    matplotlib.pyplot.yticks(fontsize=12)
    matplotlib.pyplot.xlabel('Total Distance (m)', fontsize=14)
    matplotlib.pyplot.ylabel('1km Pace (hh:mm:ss)', fontsize=14)
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.legend(title='Year', loc='best', fontsize=12)
    matplotlib.pyplot.savefig('Running_Pace_vs_Total_Distance.png')
    matplotlib.pyplot.clf()
	
# py -c 'import visualiseData; visualiseData.produceTimeDistance()'
def produceTimeDistance():
    splits = databaseAccess.getSplits()
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time']]
    y = matplotlib.dates.date2num(times)
    matplotlib.pyplot.plot( splits['total_distance'], y, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = splits['total_distance'], y = y, scatter=None, order = 2)
    matplotlib.pyplot.title('Running Pace vs. Total Distance', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Total Distance (m)', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (hh:mm:ss)', fontsize=18)
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Running_Pace_vs_Total_Distance.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceActivtyHistogram()'
def produceActivtyHistogram():
    activities = databaseAccess.getActivityDistances()
    activities.plot(kind='bar',x='nearest_5k',y='cnt',rot=45,legend=None)
    matplotlib.pyplot.title('Number of Runs per Distance', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Distance (k)', fontsize=18)
    matplotlib.pyplot.ylabel('Count of Runs', fontsize=18)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Number_of_Runs_per_Distance.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceTimePace()'
def produceTimePace():
    splits = databaseAccess.getMonthSplits()
    dates = [dateutil.parser.parse(x) for x in splits['activity_month']]
    x = matplotlib.dates.date2num(dates)
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time']]
    y = matplotlib.dates.date2num(times)
    matplotlib.pylab.plot_date(x, y, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    matplotlib.pyplot.title('Running Pace over Time', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16, rotation='vertical')
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Date', fontsize=18)
    matplotlib.pyplot.ylabel('Pace (km / hh:mm:ss)', fontsize=18)
    seaborn.regplot(x = x, y = y, scatter=None, data = splits ,order = 2)
    loc= matplotlib.dates.AutoDateLocator()
    matplotlib.pyplot.gca().xaxis.set_major_locator(loc)
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gca().xaxis.set_major_formatter(matplotlib.dates.AutoDateFormatter(loc))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Running_Pace_over_Time.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceElapsedTimeDistance()'
def produceElapsedTimeDistance():
    splits = databaseAccess.getSplits()
    lastRun = databaseAccess.getLastRun()
    splits["activity_date_dt"] = pandas.to_datetime(splits["activity_date"], format="%Y-%m-%dT%H:%M:%SZ").dt.date
    mask = splits['activity_date_dt'] == lastRun.date()
    lastRunSplits = splits.loc[mask]
    lastRunSplits = pandas.merge(lastRunSplits, lastRunSplits.groupby(['activity_id'])[['elapsed_time']].agg('sum'), on=["activity_id", "activity_id"])
    lastRunSplits['total_distance'] = lastRunSplits['total_distance'] / 1000
    splits = pandas.merge(splits, splits.groupby(['activity_id'])[['elapsed_time']].agg('sum'), on=["activity_id", "activity_id"])
    splits['total_distance'] = splits['total_distance'] / 1000
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time_y']]
    y = matplotlib.dates.date2num(times)
    max_distance = int(round(splits['total_distance'].max()))
    max_time = max(times)
    if max_distance < 42.195:
        # Assume we want to extend for a marathon
        max_distance = 42.195
        # Since we haven't run that far, assume we can finish a marathon in under 5 hours
        max_time = datetime.datetime(1970, 1, 1, 5, 0, 0)
    _, axes = matplotlib.pyplot.subplots()
    xlim = [0,max_distance]
    axes.set_xlim(xlim)
    ylim = [0,max_time]
    axes.set_ylim(ylim)
    matplotlib.pyplot.plot( splits['total_distance'], y, linestyle='', marker='o', markersize=2, alpha=0.1, color="blue")
    seaborn.regplot(x = splits['total_distance'], y = y, scatter=None, data = splits ,order = 2, ax = axes, truncate = False)
    times = [base + datetime.timedelta(seconds=x) for x in lastRunSplits['elapsed_time_y']]
    y = matplotlib.dates.date2num(times)
    matplotlib.pyplot.plot( lastRunSplits['total_distance'], y, linestyle='', marker='x', markersize=8, alpha=1, color="red")
    matplotlib.pyplot.title('Time Taken Over Distances', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Total Distance (km)', fontsize=18)
    matplotlib.pyplot.ylabel('Time Taken (hh:mm:ss)', fontsize=18)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.gca().yaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    matplotlib.pyplot.gcf().autofmt_xdate()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Time_Taken_Distance.png')
    matplotlib.pyplot.clf()


# py -c 'import visualiseData; visualiseData.produceTimeDistanceYear()'
def produceTimeDistanceYear():
    splits = databaseAccess.getSplits()
    base = datetime.datetime(1970, 1, 1, 0, 0, 0)
    times = [base + datetime.timedelta(seconds=x) for x in splits['elapsed_time']]
    years = [dateutil.parser.parse(date).year for date in splits['start_date_local']]
    unique_years = sorted(set(years))
    cmap = matplotlib.pyplot.cm.get_cmap('tab10')
    num_colors = len(unique_years)
    colors = cmap.colors[:num_colors]
    matplotlib.pyplot.figure(figsize=(10, 6))

    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Generate the year-month DataFrame for the earliest year to the latest year
    earliest_year = min(unique_years)
    earliest_date = pandas.to_datetime(f'{earliest_year}-01-01')
    end_date = pandas.to_datetime(f'{max(unique_years)}-12-31')
    year_month_df = pandas.DataFrame(pandas.date_range(start=earliest_date, end=end_date, freq='M'), columns=['activity_date'])
    year_month_df['activity_month'] = year_month_df['activity_date'].dt.strftime('%B')  # Convert to month names

    for year, color in zip(unique_years, colors):
        indices = [i for i, y in enumerate(years) if y == year]
        year_splits = splits.iloc[indices].copy()

        year_splits['activity_date'] = pandas.to_datetime(year_splits['activity_date']).dt.tz_localize(None)  # Convert 'activity_date' to datetime type
        year_splits.set_index('activity_date', inplace=True)  # Set 'activity_date' as the index

        monthly_distance_year = year_splits.groupby(pandas.Grouper(freq='M')).agg({'distance': 'sum'}) / 1000
        monthly_distance_year = monthly_distance_year.astype(int)

        # Convert 'activity_date' column to month names
        monthly_distance_year['activity_month'] = monthly_distance_year.index.strftime('%B')

        # Reset the index to remove 'activity_date' as the index column
        monthly_distance_year.reset_index(inplace=True)

        monthly_distance_year = pandas.merge(year_month_df, monthly_distance_year, how='left', on='activity_month')
        monthly_distance_year = monthly_distance_year.fillna(0)

        monthly_distance_year = monthly_distance_year.sort_values('activity_month', key=lambda x: pandas.to_datetime(x, format='%B'))  # Sort by 'activity_date'

        x = monthly_distance_year['activity_month']  # Month names as X-axis labels
        y = monthly_distance_year['distance'].values  # Distance in KM ran as Y-axis values

        # Specify the month order for the X-axis
        x = pandas.Categorical(x, categories=month_order, ordered=True)
        y = [i for i in monthly_distance_year['distance'] if i != 0]
        matplotlib.pyplot.plot(x, y, linestyle='-', marker='o', markersize=5, alpha=0.3, color=color, label=str(year))

    matplotlib.pyplot.title('Total Distance Ran by Month', fontsize=18, fontweight='bold')
    matplotlib.pyplot.xticks(fontsize=12, rotation='vertical')
    matplotlib.pyplot.yticks(fontsize=12)
    matplotlib.pyplot.xlabel('Month', fontsize=14)
    matplotlib.pyplot.ylabel('Total Distance (km)', fontsize=14)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.legend(title='Year', loc='best', fontsize=12)
    matplotlib.pyplot.savefig('Total_Distance_Ran_by_Month.png')
    matplotlib.pyplot.clf()
