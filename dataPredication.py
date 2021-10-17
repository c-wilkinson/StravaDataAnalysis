import math
import datetime

# py -c 'import dataPredication; dataPredication.getVDOT(1000, 255.0)'
def getVDOT(distance, time):
    # Swap time to minutes
    time = time / 60.0
    velocity = distance / time
    o2cost = 0.182258 * velocity + 0.000104 * velocity**2 - 4.60
    # This is the profile of an elite athlete, which I am not
    dropdead = 0.2989558 * math.exp(-0.1932605 * time) + 0.1894393 * math.exp(-0.012778 * time) + 0.8
    VDOT = o2cost / dropdead
    return VDOT

# py -c 'import dataPredication; vdot = dataPredication.getVDOT(1000, 255.0); dataPredication.getPaceRange(vdot);'
def getPaceRange(vdot):
    INTENSITY_DICTIONARY = {
        "E": (0.55, 0.65, 0.74),
        "M": (0.75, 0.79, 0.84),
        "T": (0.83, 0.86, 0.89)
    }
    paceRange = {}
    for intensityType in INTENSITY_DICTIONARY:
        intensityRange = INTENSITY_DICTIONARY[intensityType]
        range = []
        for intensity in intensityRange:
            intensityVdot = vdot * intensity
            minutesPerKM = (1 / ((29.54 + 5.000663 * intensityVdot - 0.007546 * intensityVdot**2) / 1609.34)) / 1.60934
            time = str(datetime.timedelta(minutes=minutesPerKM))
            range.append(time)
        paceRange[intensityType] = range
    return paceRange
