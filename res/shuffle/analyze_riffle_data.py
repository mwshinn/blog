# Copyright 2017 Max Shinn
# Available under the GPLv3
# http://blog.maxshinnpotential.com/2017/11/05/how-you-should-be-shuffling-cards.html

import scipy as sp
import numpy as np
import scipy.stats
import itertools

# Note that the deck I used to collect these data did not have 52
# cards.  My only real deck of cards was buried deep in a box
# somewhere, so I used a "Fact or Crap" card game which was on the top
# of the box.  Since they were approximately the same size and
# stiffness, this should not affect results.
with open("riffle_data.txt", "r") as f:
    sequences = [[int(e) for e in l.strip()] for l in f.readlines()]

splitsizes = [sum(l)/len(l) for l in sequences]

def diff(ts):
    """Return the 1st difference sequence of the binary sequence `ts`."""
    outputts = []
    for i in range(0, len(ts)-1):
        outputts.append(int(ts[i] != ts[i+1]))
    return outputts

def p_riffle_shuffle(seq, p_switch):
    """Compute the probability of my riffle shuffle model given the
    data `seq` and the parameter `p_switch`."""
    n_switches = sum(diff(seq))
    p_switches = [.5] + [p_switch]*n_switches + \
                 [1-p_switch]*(len(seq)-n_switches-1)
    return np.prod(p_switches)

def p_gsr_riffle_shuffle(seq):
    """Compute the probability of the GSR riffle shuffle model given
    the data `seq`."""
    p_handsize = sp.stats.binom.pmf(n=len(seq), p=.5, k=sum(seq))
    size_lh = sum(seq)
    size_rh = len(seq) - size_lh
    seq_copy = list(seq).copy()
    tot = 1
    while size_lh + size_rh > 0:
        if seq_copy[0] == 1:
            tot *= size_lh/(size_lh+size_rh)
            size_lh -= 1
        else:
            tot *= size_rh/(size_lh+size_rh)
            size_rh -= 1
        assert size_rh >= 0 and size_lh >= 0
        seq_copy.pop(0)
    return tot * p_handsize

assert 1 == sum(p_riffle_shuffle(s, .5) for s in list(itertools.product([0, 1], [0, 1])))
assert 1 == sum(p_riffle_shuffle(s, .8) for s in list(itertools.product([0, 1], [0, 1], [0, 1])))
assert 1 == sum(p_gsr_riffle_shuffle(s) for s in list(itertools.product([0, 1], [0, 1], [0, 1])))

# The above can be used for validation, however it turns out that we
# need to log transform for numerical stability with really small
# floating point numbers corresponding to low probabilities.

def log_p_riffle_shuffle(seq, p_switch):
    """Compute the log probability of my riffle shuffle model given 
    the data `seq` and the parameter `p_switch`."""
    n_switches = sum(diff(seq))
    p_switches = np.log([.5] + [p_switch]*n_switches + \
                        [1-p_switch]*(len(seq)-n_switches-1))
    return np.sum(p_switches)

def log_p_gsr_riffle_shuffle(seq):
    """Compute the log probability of the GSR riffle shuffle model
    given the data `seq`."""
    p_handsize = np.log(sp.stats.binom.pmf(n=len(seq), p=.5, k=sum(seq)))
    size_lh = sum(seq)
    size_rh = len(seq) - size_lh
    seq_copy = list(seq).copy()
    tot = 0
    while size_lh + size_rh > 0:
        if seq_copy[0] == 1:
            tot += np.log(size_lh/(size_lh+size_rh))
            size_lh -= 1
        else:
            tot += np.log(size_rh/(size_lh+size_rh))
            size_rh -= 1
        assert size_rh >= 0 and size_lh >= 0
        seq_copy.pop(0)
    return tot + p_handsize

# Validate log probabilities on raw probabilities on a short sequence
seq = [0, 1, 1, 0, 1, 0]
assert round(np.log(p_riffle_shuffle(seq, .8)),10) == round(log_p_riffle_shuffle(seq, .8),10)
assert round(np.log(p_gsr_riffle_shuffle(seq)),10) == round(log_p_gsr_riffle_shuffle(seq),10)

# Fit the parameter separately for each sequence, and add the
# probabilities together.
p_switch_params = []
log_prob_riffle = []
log_prob_riffle_gsr = []
bic_riffle = []
bic_gsr = []
for s in sequences:
    param = sp.optimize.differential_evolution(lambda x : -log_p_riffle_shuffle(s, x), [[0, 1]])
    p_switch_params.append(param.x[0])
    log_prob_riffle.append(-param.fun)
    log_prob_riffle_gsr.append(log_p_gsr_riffle_shuffle(s))

# Positive numbers in each indicate gsr is worse
print([r-g for r,g in zip(log_prob_riffle, log_prob_riffle_gsr)])

print(p_switch_params)

# Best fit single parameter, all sequences together (as it should be)
best_param = sp.optimize.differential_evolution(lambda x : -sum([log_p_riffle_shuffle(s, x) for s in sequences]), [[0, 1]])
aic_riffle = 2 - 2*(-best_param.fun)
aic_gsr = -2*sum([log_p_gsr_riffle_shuffle(s) for s in sequences])

print("Best parameter: %f" % best_param.x[0])
print("AIC riffle: %f, AIC GSR: %f" % (aic_riffle, aic_gsr))


