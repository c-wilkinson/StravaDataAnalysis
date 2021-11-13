import datetime
import dataPrediction

# py -c 'import coach; coach.generateCoachingPlan(1000, 255.0, 50000, 3);'
def generateCoachingPlan(raceDistance, raceTime, weeklyDistance, runsPerWeek):
    # NOTE: Race Distance and Race Time MUST be ones you've already achieved.
    # Training at a different VDOT to your own can (and probably will) cause 
    # injuries.  Ensure you build in rest days. . . the tool will let you
    # train 7 days a week every week, that doesn't mean you SHOULD.
    # The aim of this is to get you in peak condition for a "race" 18 weeks 
    # from the start of the process.
    if (runsPerWeek > 7):
        runsPerWeek = 7;
    if (runsPerWeek < 1):
        runsPerWeek = 1;
    vdot = dataPrediction.getVDOT(raceDistance, raceTime);
    paceRanges = dataPrediction.getPaceRange(vdot);
    WORKOUT_DICTIONARY = { 1 : 60, 2 : 60, 3 : 60, 4 : 60, 5 : 60, 6 : 60, 7 : 80, 8 : 80, 9 : 70, 10 : 90, 
                          11 : 90,  12 : 90, 13 : 100, 14 : 90, 15 : 100, 16 : 80, 17 : 80, 18 : 60 }
    workouts = {}
    for workoutWeek in WORKOUT_DICTIONARY:
        peakPercentage = WORKOUT_DICTIONARY[workoutWeek]
        workouts[workoutWeek] = getWorkout(workoutWeek, paceRanges, peakPercentage, weeklyDistance, runsPerWeek);

def getWorkout(weekNumber, paceRanges, peakPercentage, weeklyDistance, runsPerWeek):
    WEEKDAY_DICTIONARY = { 0 : "Monday" , 1 : "Tueday", 2 : "Wednesday", 3 : "Thursday", 4 : "Friday", 5 : "Saturday", 6 : "Sunday" };
    SPECIAL_WORKOUTS_DICTIONARY = { 7 : {1 : ("T", 20, 0)},
                                    8 : {1 : ("T", 20, 0)},
                                    9 : {1 : ("T", 20, 0)},
                                   10 : {1 : ("T", 20, 0)},
                                   11 : {1 : ("T", 20, 0)},
                                   12 : {1 : ("T", 20, 0)},
                                   13 : {1 : ("T", 20, 0)},
                                   14 : {2 : ("M", 0, 24000)},
                                   15 : {1 : ("T", 20, 0)},
                                   16 : {1 : ("T", 20, 0)},
                                   17 : {2 : ("M", 0, 22000)},
                                   18 : {1 : ("T", 20, 0)}
                                  }
    plannedDistance = weeklyDistance * (peakPercentage / 100);
    plannedDailyDistance = plannedDistance / runsPerWeek;
    REST_DICTIONARY = { 1 : (3, 0, 0, 0, 0, 0, 0),
                        2 : (1, 0, 3, 0, 0, 0, 0),
                        3 : (1, 0, 2, 0, 3, 0, 0),
                        4 : (1, 0, 1, 2, 0, 0, 3),
                        5 : (1, 2, 1, 2, 0, 0, 3),
                        6 : (1, 2, 1, 2, 1, 3, 0),
                        7 : (1, 2, 1, 2, 2, 1, 3)
                      }
    workout = {}
    week = REST_DICTIONARY[runsPerWeek];
    dow = 0;
    for day in week:
        if weekNumber in SPECIAL_WORKOUTS_DICTIONARY and runsPerWeek > 1 and day in SPECIAL_WORKOUTS_DICTIONARY[weekNumber]:
            specialWorkout = SPECIAL_WORKOUTS_DICTIONARY[weekNumber][day];
            if specialWorkout[1] == 0:
                distance = specialWorkout[2];
            else:
                distance = plannedDistance * (specialWorkout[1] / 100);
            workout[WEEKDAY_DICTIONARY[dow]] = "Work out", "Distance: {0} km".format(distance / 1000), "Pace: Between {0} per km and {1} per km".format(paceRanges[specialWorkout[0]][0], paceRanges[specialWorkout[0]][-1]);
            if plannedDistance - distance > 0:
                plannedDistance = plannedDistance - distance;
            else:
                plannedDistance = plannedDistance - (plannedDistance / (runsPerWeek - 1 / 7))
        else:
            if day == 0:
                workout[WEEKDAY_DICTIONARY[dow]] = ("Rest day", "", "")
            if day == 1 or day == 2:
                workout[WEEKDAY_DICTIONARY[dow]] = "Work out", "Distance: {0} km".format(plannedDailyDistance / 1000), "Pace: Between {0} per km and {1} per km".format(paceRanges["E"][0], paceRanges["E"][-1]);
                plannedDistance = plannedDistance - plannedDailyDistance;
            if day == 3:
                workout[WEEKDAY_DICTIONARY[dow]] = "Work out", "Distance: {0} km".format(plannedDistance / 1000), "Pace: Between {0} per km and {1} per km".format(paceRanges["E"][0], paceRanges["E"][-1]);
                plannedDistance = plannedDistance - plannedDistance;
        dow += 1;
        plannedDailyDistance = plannedDistance / (runsPerWeek - 1);
    print(workout)