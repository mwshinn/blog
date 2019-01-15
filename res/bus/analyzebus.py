# This script is to analyze the times for the Yale bus routes
# generated by "getyalebus.py", but should work with any data file in
# the format described in "getyalebus.py".

# Copyright 2016 Max Shinn <max@maxshinnpotential.com>
# Available under the GPLv3

import pandas
import random # for bus ids

# PARAMETERS
# ==========

# DATA_FILE = "2016-07-22-data.csv"
# DATA_FILE = "2016-07-26-data.csv"
DATA_FILE = "2016-07-28-data.csv"

# VARIABLES
# =========

df = pandas.read_csv(DATA_FILE)
df['timestamp'] = pandas.to_datetime(df['timestamp'], unit="s")
df.index = df['timestamp']

# Generate a list of stop ids from the column headers
stops = list(map(lambda x : x[0:-1], list(df.columns)[1::2]))

# FUNCTIONS
# =========

# swap_lists_before takes the first `i` elements of list `l1` and
# switches them with the first `i` elements of list `l2`.  Both lists
# are modified in-place.  `i` must be an integer, and both `l1` and
# `l2` must have at least `i` elements
def swap_lists_before(l1, l2, i):
    assert type(i) == int and type(l1) == list and type(l2) == list, "Wrong datatypes"
    assert len(l1) >= i and len(l2) >= i
    bl1 = []
    bl2 = []
    for _i in range(0, i):
        bl1.append(l1.pop(0))
        bl2.append(l2.pop(0))
    # the .extend() function only works on the right, so we reverse to make it work on the left
    l1.reverse()
    l2.reverse()
    bl1.reverse()
    bl2.reverse()
    l1.extend(bl2)
    l2.extend(bl1)
    l1.reverse()
    l2.reverse()

# has_jump determines if there is a jump in the timeseries.  Many of
# the times seem to be unreliable, as buses seem to disappear and
# reappear in the analysis.  These data are not reliable so we exclude
# them.
def has_jump(l):
    for i in range(0, len(l)-1):
        if abs(l[i]-l[i+1]) >=3:
            return True
    return False

# did_bus_arrive_here takes two pairwise elements of a list and
# determines whether or not the bus arrived in between them.  `e1`
# should come before `e2` temporally/sequentially.
def did_bus_arrive_here(e1, e2):
    return e1 in [0, 1, 2] and e2-e1 >= 5

# MAIN CODE
# =========

# First, make it so that a single bus is only in one list.  This
# creates two lists of buses and their distance from the stop.  After
# a bus arives in a list, that list switches to the second next
# ariving bus (since the next one will be in the other list).
for s in stops:
    l1 = list(df[s+"a"])
    l2 = list(df[s+"b"])
    for i in range(0, len(l1)-1):
        # l1 will always contain the next arriving bus.  So, we detect
        # places where the bus arrives, and swap it so that the same
        # bus is in the same column.
        if did_bus_arrive_here(l1[i], l1[i+1]):
            swap_lists_before(l1, l2, i+1)
    df[s+"a"] = l1
    df[s+"b"] = l2

# Split the lists up into single bus sequences.  Create a dictionary
# of lists of pandas timeseries.  Each dictionary key should be the
# stop id.  The list's elements represent different buses that come to
# that stop, and the amount of time until they arrive.  Each
# timeseries should, therefore, start at a high number and slowly go
# down to 1.
buses = {}
for s in stops:
    buses[s] = []
    for l in [df[s+"a"], df[s+"b"]]:
        busstart = 0
        for i in range(0, len(l)-1):
            if did_bus_arrive_here(l[i], l[i+1]):
                buses[s].append(l[busstart:i+1])
                busstart = i+1
                
# In this analysis, the arrival time is taken to be the last time in
# the list.  This is not fully accurate, as the data are only
# collected in 10 second incements (by default).  At the very least we
# should apply a continuity correction of 5 seconds, however if there
# was a hiccup in the data (e.g. the connection timed out a few times)
# then it will get off this 10 second mark, and anything over this gap
# will require a different continuity correction.  For simplicity, I
# ignore the continuity correction.  Also, this will eliminate the
# bugs caused if the data are collected at different increments.

# The unit used here for analysis is seconds.  This is less than
# ideal, because the predictions to not have this precision.  However,
# I think too much precision here is better than too little,
# especially since we don't know how the minute-wise prediction was
# calculated from transloc.com's internal prediction which is
# presumably in seconds or milliseconds.

# Here we calculate, in seconds, the error of each prediction in the
# list.  We create a list of tuples in the following format:
#
#    (stop_id, bus_id, predicted_elapsed_time, actual_elapsed_time, prediction_difference, arrival_time, predicted_arrival_time)
#
# The bus_id is randomly generated.  The predicted_elapsed_time is the
# predicted number of seconds until the bus arrives.  The actual
# elapsed_time is the actual amount of time it took the bus to arrive.
# The prediction_difference is the predicted_elapsed_time minus the
# actual_elapsed_time.  The arrival_time is the timestamp (in pandas'
# datetime format) of when the bus did arrive.  predicted_arrival_time
# is the time of day (in pandas' datetime format) of when the bus was
# supposed to arrive.
#
# We also make a version of the predictions without the jumps.  The
# jumps are usually due to poor data qualtiy.  The most common reason
# for this seems to be when one bus goes off the radar for a minute or
# two.  This causes shifts in the two columns of recorded data.  While
# a more sophisticated algorithm could correct for this, I do it here
# the easy way.  This does slightly bias the data but it will do for
# now.
_predictions = []
_predictionsnj = [] # Excluding the timeseries which contain a jump

for s in stops:
    for b in buses[s]:
        if b[-1] != 1: continue # The bus never arrived.  It's probably the last one in the series.
        hasjump = has_jump(b)
        stop_id = s
        bus_id = random.randint(0, 2**31)
        arrival_time = b.index[-1]
        for i in range(0, len(b)):
            predicted_elapsed_time = b[i]*60
            actual_elapsed_time = (arrival_time - b.index[i]).seconds
            prediction_difference = predicted_elapsed_time - actual_elapsed_time
            predicted_arrival_time = b.index[i] + pandas.to_timedelta(predicted_elapsed_time, unit="s")
            _predictions.append((stop_id, bus_id, predicted_elapsed_time, actual_elapsed_time, prediction_difference, arrival_time, predicted_arrival_time))
            if not hasjump:
                _predictionsnj.append((stop_id, bus_id, predicted_elapsed_time, actual_elapsed_time, prediction_difference, arrival_time, predicted_arrival_time))
                if numpy.abs(prediction_difference)>500:
                    print(list(b), prediction_difference)

predictions = pandas.DataFrame(_predictions, columns=["stop_id", "bus_id", "predicted_elapsed_time", "actual_elapsed_time", "prediction_difference", "arrival_time", "predicted_arrival_time"])
predictionsnj = pandas.DataFrame(_predictionsnj, columns=["stop_id", "bus_id", "predicted_elapsed_time", "actual_elapsed_time", "prediction_difference", "arrival_time", "predicted_arrival_time"])


# predictionsnj.plot.scatter("predicted_elapsed_time", "prediction_difference")
# sns.heatmap(predictionsnj.pivot_table("prediction_difference", "stop_id", "predicted_elapsed_time"), log=True)
# sns.boxplot(data=predictionsnj, x="stop_id", y="prediction_difference")
# sns.lmplot(data=predictionsnj, x="predicted_elapsed_time", y="actual_elapsed_time")

# What percentage of the data are we keeping?
len(predictionsnj)/len(predictions)

# The scatter plot of predicted vs actual time looks about like what
# we would expect.
predictionsnj.plot.scatter(x="predicted_elapsed_time", y="actual_elapsed_time")

# Among stops with a reasonable number of data points, the variance
# doesn't change much.
for s in stops:
    if len(predictionsnj["prediction_difference"][predictionsnj["stop_id"]==s]) < 300: continue
    print(len(predictionsnj["prediction_difference"][predictionsnj["stop_id"]==s]))
    print(numpy.var(predictionsnj["prediction_difference"][predictionsnj["stop_id"] == s]/60))

# Plotting the mean and variance when the bus is at least m minutes
# away.  It drops down at the end due to a lack of data, not due to a
# true effect.  I think around 10 minutes or later would be good to
# use when calculating variance for purely practical reasons, as you
# can't plan ahead of time to catch something if it is too near in the
# future, which defeats the purpose of the present analysis.
meanat = lambda m : numpy.mean(predictionsnj["prediction_difference"][predictionsnj["predicted_elapsed_time"]>m*60]/60)
varat = lambda m : numpy.var(predictionsnj["prediction_difference"][predictionsnj["predicted_elapsed_time"]>m*60]/60)
m = list(range(1, 20))
ym = [meanat(x) for x in m]
yv = [varat(x) for x in m]
plt.plot(m, yv); plt.title("Variance in prediction difference when bus is at least x minutes away"); plt.show()
plt.errorbar(m, ym, yerr=yv); plt.show()

# There does not seem to be a strong time dependence on the variance
predictionsnj.plot("arrival_time", "prediction_difference")

# So, using all of the data, the best estimate of the variance is
print(numpy.var(predictionsnj["prediction_difference"]/60))

# Using only data whereby the bus is still at least 10 minutes away, we have
print(numpy.var(predictionsnj["prediction_difference"][predictionsnj["predicted_elapsed_time"]>10*60]/60))

# It is not perfectly normal, but it is close enough, especially
# seeing as the skew is to the left, where the bus will take longer
# than expected, which isn't as big of a deal as the other way around.

plt.figure(figsize=[14, 6])
sns.set_style("white")
sns.set_context("poster")
plt.subplot(1,2,1)
sns.distplot((predictionsnj["prediction_difference"][predictionsnj["predicted_elapsed_time"]>10*60]/60), fit=scipy.stats.distributions.norm)
plt.xlabel("Prediction difference (predicted minus actual, minutes)")
sns.despine()
plt.subplot(1,2,2)
scipy.stats.probplot((predictionsnj["prediction_difference"][predictionsnj["predicted_elapsed_time"]>15*60]/60), dist="norm", plot=plt, fit=False)
sns.despine()
plt.gcf().subplots_adjust(bottom=0.15)
plt.savefig("isnormal.png")
plt.show()



# For this dataset, another interesting analysis would be to find
# whether the real-time prediction is a better predictor than the
# expected arrival time
