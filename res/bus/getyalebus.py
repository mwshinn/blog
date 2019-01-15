# This is a script for Python3 to download the times for the Yale bus
# routes.  In theory, this should work for any bus route that uses
# transloc.com.

# Copyright 2016 Max Shinn <max@maxshinnpotential.com>
# Available under the GPLv3

from bs4 import BeautifulSoup
import requests
import numpy
import time # For the timestamp
import re # To set up dataframe

# PARAMETERS
# ==========

# Page link of the route to crawl
ROUTE_PAGE = "http://yale.transloc.com/t/routes/4000346"
#ROUTE_PAGE = "http://yale.transloc.com/t/routes/4000378"

# How often to ping the website, in seconds.
UPDATE_PERIOD = 10

# How long to collect data for, in minutes
DURATION = 60*8


# The data we collect over this session will be saved here.  The first
# column is "timestamp", and the rest are the stop ids, suffixed by
# "a" or "b" for the next and the second next bus.  Note that when the
# "a" bus arrives, the time for the "b" bus will switch to the "a"
# column.
#
# Make sure you change this before running the script twice or it will
# overwrite the previous "data.csv" file!
DATA_FILE = "data.csv"


# VARIABLES
# =========

# The http session.  Doesn't require anything special since we just
# need POST.
s = requests.Session()


# First we need to find the number of columns.
page = s.post(ROUTE_PAGE).text
stopids_ = re.findall('/t/stops/([0-9]+)', page)
stopids = [s for i,s in enumerate(stopids_) if stopids_.index(s) == i]
# `cols` lists each stop id twice in a row, once followed by "a" and
# once followed by "b".
cols = ["timestamp"] + list([v for a in zip(map(lambda x:x+"a", stopids), map(lambda x:x+"b", stopids)) for v in a])
# `times` is a list of lists.  Each sublist should follow the format
# described above, with the exception of the first row, which IS the
# above list.  In other words, the first element in each sublist
# should be the timestamp, and then each stop as indexed above should
# have the times listed at the given timestamp.  Since `times` will be
# written as a csv file, the first line (`cols`) is the header.
times = [cols]

# Default timestamp
timestamp = int(time.time()) # This will be updated throughout the loop.
initial_timestamp = timestamp # Used to determine stopping times

while True:
    if initial_timestamp + 60*DURATION < int(time.time()): break
    # Run every UPDATE_PERIOD seconds.  This is better than sleeping
    # for UPDATE_PERIOD because the script itself takes a small amount
    # of time to run, so it ensures it will always stay in sync.
    while timestamp + UPDATE_PERIOD > int(time.time()):
        time.sleep(.5)
        
    timestamp = int(time.time())

    page = s.post(ROUTE_PAGE).text

    # We need the html.parser parser because the lxml default doesn't read
    # the invalid html on this page (namely the unescaped "<")
    soup = BeautifulSoup(page, "html.parser") 
    
    # This is a dictionary of lists, indexed by stop id, and with a value
    # of the next two bus times listed for that stop.
    stoptimes = {}
    # Despite what it claims, this is not beautiful.  It's a ton of html
    # parsing code that Just Works(R).  Don't touch unless you need to.
    tds = soup.find_all("td", attrs={"class": "wait_time"})
    for t in tds:
        stopid = t.findChild("a").attrs['href'].split("/").pop()
        waittimes = t.findChild("span", attrs={"class": "time_1"}).text.strip().replace(" ", "").replace("<", "").replace("mins", "").replace("min", "").replace("-", "").split("&")
        assert len(waittimes) <= 2, "Invalid time parsing" # The website only lists the next two times, so this should be 0, 1, or 2 elements.
        stoptimes[stopid] = waittimes

    # Build up a list (`thisrow`) which represents a single row of the csv file to write.
    thisrow = [timestamp]
    for col in cols:
        if col == "timestamp": continue
        if col[-1:] == "b": continue # In `cols`, the "b" version always follows the "a" version so we can ignore it.
        colid = col[0:-1]
        if not colid in stoptimes.keys():
            thisrow.append(99999)
            thisrow.append(99999)
            continue
        thisrow.append(stoptimes[colid][0] if stoptimes[colid][0] != '' else 99999) # The list was empty, i.e. no more buses at this stop today.
        thisrow.append(99999 if len(stoptimes[colid]) != 2 or stoptimes[colid][1] == '' else stoptimes[colid][1]) # THere was only one element in the list, i.e. only one more bus today.
    
    times.append(thisrow) # Add the present row to the full csv file we will be writing
    print(thisrow)
    with open(DATA_FILE, "w") as f:
        # Ad-hoc csv file for nested lists
        f.write("\n".join(map(",".join, [[str(e) for e in r] for r in times])))
