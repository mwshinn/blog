# Model code for "Are buffets efficient?"
# Copyright 2019 Max Shinn <max@maxshinnpotential.com>

import paranoid as pns
import numpy as np
import scipy as sp
import scipy.stats
import random
import names
import pandas
import matplotlib.pyplot as plt
import seaborn as sns

@pns.returns(pns.Positive)
def get_random_dish_speed():
    return sp.stats.gamma.rvs(a=10, scale=.1)

@pns.returns(pns.Positive)
def get_random_speed():
    return sp.stats.gamma.rvs(a=10, scale=.1)


class Dish:
    """A single dish in a buffet.

    Maintains two variables:

    - `speed` - A constant describing the rate at which this dish is consumed.
    - `queue` - A list describing people waiting in line to serve themselves this dish.
    """
    def __init__(self, speed=None, p_want=.8, name=None):
        if speed is None:
            speed = get_random_dish_speed()
        self.speed = speed
        self.p_want = p_want
        self.queue = []
        if name is None:
            name = "dish%i" % int(np.random.rand()*10000)
        self.name = name
    def __repr__(self):
        return self.name        
    def add_to_queue(self, person, time):
        """Put a person `person` at the end of this dish's queue.  `time` is current (sim) time."""
        self.queue.append(person)
        if len(self.queue) == 1:
            person.start_serving(self, time)
    def check_queue(self, time):
        """Update queue status.

        If queue is empty, return None.  

        If not, check to see if the first person in the queue is done
        serving themself.  If not, do nothing.  If so, send the
        appropriate signal to this person object, remove this person
        object from the queue, and send a signal to the next person
        object in the queue to start serving themself.

        `time` should be the current (simulation) time.
        """
        if not self.queue:
            return None
        if self.queue[0].check_if_done_serving(time):
            if len(self.queue) > 1:
                self.queue[1].start_serving(self, time)
            return self.queue.pop(0)

class Person:
    """A person at a buffet.

    Maintains information about the dishes they would like to eat
    (`wants`), a constant describing their speed (`speed`), and the
    time it takes them to serve for each dish `dishtimes`, which is
    precomputed.
    """
    def __init__(self, wants, speed=None):
        if speed is None:
            speed = get_random_speed()
        self.speed = speed
        self.wants = wants
        self.current_dish = None
        self.dishtimes = {}
        for d in wants:
            self.dishtimes[d] = self.get_dish_wait_time(d)
        # Statistics
        self.total_serving_time = sum([self.dishtimes[d] for d in self.wants])
        self.wanted = wants.copy()
        self.name = names.get_first_name()
        self.total_waiting_time = 0
        self.dishwaits = {}
    def __repr__(self):
        return self.name
    def get_dish_wait_time(self, d):
        """Return a sample from some distribution to determine serving time."""
        scale_param = self.speed*d.speed
        return sp.stats.lognorm.rvs(1)*scale_param
    def is_serving(self):
        """Is the person currently serving themselves, i.e. at the front of a queue."""
        return (self.current_dish is not None)
    def start_serving(self, d, time):
        """Start serving from dish `d`."""
        assert not self.is_serving()
        self.current_dish = d
        self.start_time = time
    def check_if_done_serving(self, time):
        """If done serving, reset appropriate object variables and return True.  Else return False."""
        assert self.is_serving()
        if self.current_dish not in self.dishtimes.keys():
            self.current_dish = None
            self.start_time = 0
            return True
        if time >= self.start_time + self.dishtimes[self.current_dish]:
            prev_dish = self.current_dish
            self.current_dish = None
            self.start_time = 0
            self.wants.pop(self.wants.index(prev_dish))
            if len(self.wants) == 0:
                self.total_waiting_time = time
            return True
        return False
    def choose_next_dish(self):
        """Decide which one to go to next and return it.  If none left, return None."""
        if not self.wants:
            return None
        shortest = next(iter(sorted(self.wants, key=lambda x : len(x.queue))))
        return shortest


TIMESTEP = .01

def init_dishes_people(n_wanted=None, p_wanted=.8, n_people=100, n_dishes=6):
    """Create two lists: one of Person objects and the other of Dish
    objects, with each one "linked" to the other.  Return a tuple of
    ([dish objects], [people objects]).
    """
    if p_wanted is not None and n_wanted is None:
        DISHES = [Dish(p_want=p_wanted) for _ in range(0, n_dishes)]
        PEOPLE = [Person(wants=[d for d in DISHES if np.random.rand() < d.p_want]) for _ in range(0, n_people)]
    elif p_wanted is None and n_wanted is not None:
        DISHES = [Dish() for _ in range(0, n_dishes)]
        PEOPLE = [Person(wants=random.sample(DISHES, n_wanted)) for _ in range(0, n_people)]
    else:
        raise ValueError("Invalid function argument")
    return (DISHES, PEOPLE)

def run_separate_queues(DISHES, PEOPLE):
    """Simulate using a separate queue for each dish"""
    # Init the people and dishes
    for p in PEOPLE:
        dish = p.choose_next_dish()
        if dish is not None:
            dish.add_to_queue(p, time=0)
    
    # Run the simulation        
    t = 0
    while True:
        if all(not d.queue for d in DISHES):
            break
        for d in DISHES:
            person = d.check_queue(t)
            if person is not None:
                dish = person.choose_next_dish()
                if dish is not None:
                    dish.add_to_queue(person, time=t)
        t += TIMESTEP
    return (DISHES,PEOPLE)

def run_single_queue(DISHES, PEOPLE):
    """Simulate using a single queue for all dishs"""
    # Init the people and dishes
    for p in PEOPLE:
        DISHES[0].add_to_queue(p, time=0)
    
    # Run the simulation        
    t = 0
    while True:
        if all(not d.queue for d in DISHES):
            break
        for i in range(0, len(DISHES)):
            person = DISHES[i].check_queue(t)
            if person is not None and i < len(DISHES)-1:
                DISHES[i+1].add_to_queue(person, time=t)
        t += TIMESTEP
    return (DISHES,PEOPLE)

def run_sims(run_func="separate", N=100, p_want=.8, n_people=100, n_dishes=6):
    """Simulate many runs and collect the results into a dict for simple analysis"""
    f = run_separate_queues if run_func == "separate" else run_single_queue if run_func == "single" else None
    runs = []
    for i in range(0, N):
        print("Running %i" % i)
        DISHES, PEOPLE = f(*init_dishes_people(p_wanted=p_want, n_people=n_people, n_dishes=n_dishes))
        stats = {"max_wait": max(p.total_waiting_time for p in PEOPLE),
                 "min_wait": min(p.total_waiting_time for p in PEOPLE),
                 "mean_wait": np.mean([p.total_waiting_time for p in PEOPLE]),
                 "median_wait": np.quantile([p.total_waiting_time for p in PEOPLE], .5),
                 "1st_quart_wait": np.quantile([p.total_waiting_time for p in PEOPLE], .25),
                 "3rd_quart_wait": np.quantile([p.total_waiting_time for p in PEOPLE], .75),
                 "fastest_dish_speed": min(d.speed for d in DISHES),
                 "slowest_dish_speed": max(d.speed for d in DISHES),
                 "mean_dish_speed": np.mean([d.speed for d in DISHES]),
                 "slowest_person_speed": min([1/p.speed for p in PEOPLE]),
                 "mean_person_speed": np.mean([1/p.speed for p in PEOPLE]),
                 "p_want": p_want,
                 "run_func": run_func,
        }
        runs.append(stats)
    return runs

# Set up the colors we will use for plotting
pal = sns.color_palette()

# Simulate for different probabilities of wanting a given dish
sims = run_sims("separate", N=100)
sims2 = run_sims("single", N=100)
sims3 = run_sims("separate", N=100, p_want=.3)
sims4 = run_sims("single", N=100, p_want=.3)
sims5 = run_sims("separate", N=100, p_want=1)
sims6 = run_sims("single", N=100, p_want=1)

# Combine all simulations into a pandas data frame
df = pandas.DataFrame(sims+sims2+sims3+sims4+sims5+sims6)
# Create more sensible names for the columns
df["Inequality"] = df["3rd_quart_wait"] - df["1st_quart_wait"]
df.rename(columns={'p_want': 'Probability of wanting a dish',
                   'mean_wait': 'Mean wait time',
                   'run_func': 'Buffet type'}, inplace=True)

# Make a bar plot of the simulations with default parameters
ax = plt.subplot(2,1,1)
agg = df.groupby(["Buffet type", "Probability of wanting a dish"])["Mean wait time"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.xlabel("")
plt.ylabel("Mean wait time")
ax = plt.subplot(2,1,2)
agg = df.groupby(["Buffet type", "Probability of wanting a dish"])["Inequality"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.ylabel("Inequality")
ax.get_legend().remove()
plt.tight_layout()
plt.savefig("wait-ineq-few-dishes.png")
plt.show()

# Repeat all of the above, but for many dishes
sims = run_sims("separate", N=100, p_want=.1, n_dishes=20)
sims2 = run_sims("single", N=100, p_want=.1, n_dishes=20)
sims3 = run_sims("separate", N=100, p_want=.2, n_dishes=20)
sims4 = run_sims("single", N=100, p_want=.2, n_dishes=20)
sims5 = run_sims("separate", N=100, p_want=.3, n_dishes=20)
sims6 = run_sims("single", N=100, p_want=.3, n_dishes=20)
sims7 = run_sims("separate", N=100, p_want=.4, n_dishes=20)
sims8 = run_sims("single", N=100, p_want=.4, n_dishes=20)

dfmd = pandas.DataFrame(sims+sims2+sims3+sims4+sims5+sims6+sims7+sims8)
dfmd["Inequality"] = dfmd["3rd_quart_wait"] - dfmd["1st_quart_wait"]

dfmd.rename(columns={'p_want': 'Probability of wanting a dish',
                   'mean_wait': 'Mean wait time',
                   'run_func': 'Buffet type'}, inplace=True)
ax = plt.subplot(2,1,1)
agg = dfmd.groupby(["Buffet type", "Probability of wanting a dish"])["Mean wait time"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.xlabel("")
plt.ylabel("Mean wait time")
ax = plt.subplot(2,1,2)
agg = dfmd.groupby(["Buffet type", "Probability of wanting a dish"])["Inequality"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.ylabel("Inequality")
ax.get_legend().remove()
plt.tight_layout()
plt.savefig("wait-ineq-many-dishes.png")
plt.show()

# Repeat all of the above, but for many people
sims = run_sims("separate", N=100, n_people=500)
sims2 = run_sims("single", N=100, n_people=500)
sims3 = run_sims("separate", N=100, p_want=.3, n_people=500)
sims4 = run_sims("single", N=100, p_want=.3, n_people=500)
sims5 = run_sims("separate", N=100, p_want=1, n_people=500)
sims6 = run_sims("single", N=100, p_want=1, n_people=500)

dfmp = pandas.DataFrame(sims+sims2+sims3+sims4+sims5+sims6)
dfmp["Inequality"] = dfmp["3rd_quart_wait"] - dfmp["1st_quart_wait"]

dfmp.rename(columns={'p_want': 'Probability of wanting a dish',
                   'mean_wait': 'Mean wait time',
                   'run_func': 'Buffet type'}, inplace=True)
ax = plt.subplot(2,1,1)
agg = dfmp.groupby(["Buffet type", "Probability of wanting a dish"])["Mean wait time"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.xlabel("")
plt.ylabel("Mean wait time")
ax = plt.subplot(2,1,2)
agg = dfmp.groupby(["Buffet type", "Probability of wanting a dish"])["Inequality"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.ylabel("Inequality")
ax.get_legend().remove()
plt.tight_layout()
plt.savefig("wait-ineq-many-people.png")
plt.show()

# Repeat all of the above, but for many very few people
sims = run_sims("separate", N=100, n_people=30)
sims2 = run_sims("single", N=100, n_people=30)
sims3 = run_sims("separate", N=100, p_want=.3, n_people=30)
sims4 = run_sims("single", N=100, p_want=.3, n_people=30)
sims5 = run_sims("separate", N=100, p_want=1, n_people=30)
sims6 = run_sims("single", N=100, p_want=1, n_people=30)

dffp = pandas.DataFrame(sims+sims2+sims3+sims4+sims5+sims6)
dffp["Inequality"] = dffp["3rd_quart_wait"] - dffp["1st_quart_wait"]

dffp.rename(columns={'p_want': 'Probability of wanting a dish',
                   'mean_wait': 'Mean wait time',
                   'run_func': 'Buffet type'}, inplace=True)
ax = plt.subplot(2,1,1)
agg = dffp.groupby(["Buffet type", "Probability of wanting a dish"])["Mean wait time"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.xlabel("")
plt.ylabel("Mean wait time")
ax = plt.subplot(2,1,2)
agg = dffp.groupby(["Buffet type", "Probability of wanting a dish"])["Inequality"].agg([np.mean, scipy.stats.sem])
agg['mean'].unstack(0).plot(kind='bar', yerr=agg['sem'].unstack(0), ax=ax, rot=0, color=pal)
plt.ylabel("Inequality")
ax.get_legend().remove()
plt.tight_layout()
plt.savefig("wait-ineq-veryfew-people.png")
plt.show()

def run_sims_people(run_func="separate", N=100, p_want=.8, n_people=100, n_dishes=6):
    """Simulate many times and create statistics on the number of people.

    This is an alternative to run_sims, except it tabulates for
    individual people.  It also returns a DataFrame.
    """
    f = run_separate_queues if run_func == "separate" else run_single_queue if run_func == "single" else None
    people = [] # run, speed, waiting time
    for i in range(0, N):
        print("Running %i" % i)
        DISHES, PEOPLE = f(*init_dishes_people(p_wanted=p_want, n_people=n_people, n_dishes=n_dishes))
        for p in PEOPLE:
            people.append((i, p.speed, len(p.wanted), run_func, p.total_waiting_time))
    return pandas.DataFrame(people, columns=["run_id", "Speed", "# dishes wanted", "Buffet type", "Total waiting time"])

# Look at simulations in which we keep track of people instead of
# entire runs.
sep = run_sims_people("separate", N=30)
single = run_sims_people("single", N=30)
peo = pandas.concat([sep, single])

# Get rid of people who only want one dish, as there are not very many
# of them so it is mostly noise.
peo = peo[peo["# dishes wanted"] > 1]

# Plot the wait time for people who want different numbers of dishes.
sns.barplot(data=peo, x="Buffet type", y="Total waiting time", hue="# dishes wanted")
plt.savefig("fairness.png")
plt.show()

# Examine how an individual's speed compares to their waiting time.
plt.figure(figsize=(4,4))
sns.scatterplot(data=peo.sample(frac=1), x="Speed", y="Total waiting time", hue="Buffet type", markers=".", s=8, ax=plt.gca())
sns.despine()
plt.tight_layout()
plt.savefig("speed-vs-time.png")
plt.show()
# Show they are not correlated.
scipy.stats.spearmanr(peo['Speed'], peo['Total waiting time'])
