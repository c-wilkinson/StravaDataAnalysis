import pandas
import dateutil
import datetime
import seaborn
import matplotlib
import matplotlib.pylab
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