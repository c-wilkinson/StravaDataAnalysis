import numpy
import pandas
import dateutil
import seaborn
import matplotlib
import matplotlib.pylab
import databaseAccess

# py -c 'import visualiseData; visualiseData.produceTimeElevation()'
def produceTimeElevation():
    splits = databaseAccess.getSplits()
    matplotlib.pyplot.plot( 'elevation_difference', 'elapsed_time', data=splits, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = 'elevation_difference', y = 'elapsed_time', scatter=None, data = splits ,order = 2)
    matplotlib.pyplot.title('Running Pace vs. Elevation Change', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Elevation Change (m)', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (sec)', fontsize=18)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Running_Pace_vs_Elevation_Change.png')
    matplotlib.pyplot.clf()

# py -c 'import visualiseData; visualiseData.produceTimeDistance()'
def produceTimeDistance():
    splits = databaseAccess.getSplits()
    matplotlib.pyplot.plot( 'total_distance', 'elapsed_time', data=splits, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = 'total_distance', y = 'elapsed_time', scatter=None, data = splits ,order = 2)
    matplotlib.pyplot.title('Running Pace vs. Total Distance', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Total Distance (m)', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (sec)', fontsize=18)
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
    y = splits['elapsed_time']
    matplotlib.pylab.plot(x, y, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    matplotlib.pyplot.title('Running Pace over Time', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16, rotation='vertical')
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Date', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (sec)', fontsize=18)
    matplotlib.pyplot.tight_layout()
    z = numpy.polyfit(x, y, 1)
    p = numpy.poly1d(z)
    polyX = numpy.linspace(x.min(), x.max(), 100)
    matplotlib.pylab.plot(polyX,p(polyX),"r")
    loc= matplotlib.dates.AutoDateLocator()
    matplotlib.pyplot.gca().xaxis.set_major_locator(loc)
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
    max_distance = int(round(splits['total_distance'].max()))
    max_time = int(round(splits['elapsed_time_y'].max()))
    if max_distance < 42.195:
        # Assume we want to extend for a marathon
        max_distance = 42.195
        # Since we haven't run that far, assume we can finish a marathon in under 5 hours
        max_time = 18000
    _, axes = matplotlib.pyplot.subplots()
    xlim = [0,max_distance]
    axes.set_xlim(xlim)
    ylim = [0,max_time]
    axes.set_ylim(ylim)
    matplotlib.pyplot.plot( 'total_distance', 'elapsed_time_y', data=splits, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = 'total_distance', y = 'elapsed_time_y', scatter=None, data = splits ,order = 2, ax = axes, truncate = False)
    matplotlib.pyplot.title('Time Taken Over Distances', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Total Distance (km)', fontsize=18)
    matplotlib.pyplot.ylabel('Time Taken (sec)', fontsize=18)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.savefig('Time_Taken_Distance.png')
    matplotlib.pyplot.clf()