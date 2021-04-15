import seaborn
import matplotlib
import databaseAccess

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