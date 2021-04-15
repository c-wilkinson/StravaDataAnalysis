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
    matplotlib.pyplot.savefig('Running_Pace_vs_Elevation_Change.png')

def produceTimeElevation():
    splits = databaseAccess.getSplits()
    matplotlib.pyplot.plot( 'total_distance', 'elapsed_time', data=splits, linestyle='', marker='o', markersize=5, alpha=0.1, color="blue")
    seaborn.regplot(x = 'total_distance', y = 'elapsed_time', scatter=None, data = splits ,order = 2)
    matplotlib.pyplot.title('Running Pace vs. Total Distance', fontsize=18, fontweight="bold")
    matplotlib.pyplot.xticks(fontsize=16)
    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xlabel('Total Distance (m)', fontsize=18)
    matplotlib.pyplot.ylabel('1km Pace (sec)', fontsize=18)
    matplotlib.pyplot.savefig('Running_Pace_vs_Total_Distance.png')