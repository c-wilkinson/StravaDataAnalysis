import numpy
import functools
import datetime
import databaseAccess
import pandas

def getCoefficientArray(month=0):
    splits = databaseAccess.getSplits()
    if month > 0:
        splitDate = datetime.date.today() - pandas.offsets.DateOffset(months=month)
        splitDateStr = splitDate.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f'Date to look from {splitDate}')
        splits = splits[(splits.activity_date >= splitDateStr)]
    coeff = numpy.polyfit(splits['elevation_difference'], splits['elapsed_time'], 2)
    return coeff

def predicateRun(distance, coeff):
    # Predicts time on a completely flat track
    time = coeff[0]**2+coeff[1]+ coeff[2]
    # Multiply time by distance
    time = time * distance
    # Change time to minutes
    predicatedTime = "%02d:%02d:%02d.%03d" % functools.reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],[(round(time*1000),),1000,60,60])
    return predicatedTime