import random
import matplotlib.pyplot as plt
import seaborn as sns
import numpy, scipy
import math

# Allow our recursive function
import sys
sys.setrecursionlimit(10001)

def asstring(ts):
    """Convert a binary sequence from a list to a string."""
    return "".join([str(i) for i in ts])

def ordinal(num):
    """Convert n integer to its linguistic ordinal form (a string)."""
    if num == 1:
        return "1st"
    if num == 2:
        return "2nd"
    if num == 3:
        return "3rd"
    else:
        return str(num)+"th"

def mean(x):
    "Find the mean (symbol probability) of a binary sequence."
    return sum([int(i) for i in x])/len(x)

def diff(ts):
    """Return the 1st difference sequence of the binary sequence `ts`."""
    outputts = []
    for i in range(0, len(ts)-1):
        outputts.append(int(ts[i] != ts[i+1]))
    return outputts

def nthdiff(ts, n):
    """Return the `n`'th difference sequence of binary sequence `ts`."""
    if n == 0:
        return ts
    else:
        return nthdiff(diff(ts), n-1)

def integrate(ts, start=0):
    """Return  the first integral sequence of the binary sequence `ts`.

    In other words, given a diff sequence, construct a binary sequence
    that would have that diff.  The first digit should be `start`,
    which should have a value of 0 or 1.
    """
    outputts = [start]
    for e in ts:
        outputts.append(int(bool(int(e)) != bool(int(outputts[-1])))) # XOR
    return outputts

def human_random(l=1000, switch_prob=.5):
    """Generate a human-like random binary sequence.

    Humans tend to have a higher than average switch probability.
    Here, generate a sequence of length `l` with a switch probability
    of `switch_prob`.  When `switch_prob` = 5, this is a typical
    pseudo-random sequence.
    """
    ts = [random.randint(0, 1)]
    for i in range(0, l-1):
        if random.random() > switch_prob:
            ts.append(ts[i])
        else:
            ts.append(1-ts[i])
    return ts

def autocorrelate(ts):
    """Find the autocorelation of the binary sequence `ts`."""
    # Convert to correct datatype (int for binary sequences)
    ts = list(map(int, ts))
    # Autocorrelation function shortcut w/ numpy
    acf = numpy.correlate(ts, ts, mode="full")
    # Normalize by size of overlap
    normfactor = list(range(1, len(ts))) + list(range(len(ts), 0, -1))
    acf = acf/normfactor
    return acf[acf.size//2:]

def nthentropy(s, o=1):
    # Convert `s` to a string
    s = "".join(map(str, s))
    # Pad the string to make an even multiple of the code length
    while len(s) % o != 0: s = s + "0"
    # Split into codewords
    codewords = [s[i*o:i*o+o] for i in range(0, len(s)//o)]
    # Find codeword frequencies
    freqs = { c : codewords.count(c)/len(codewords) for c in set(codewords) }
    # And return entropy
    _H = lambda x : - x * math.log2(x)
    return sum(map(_H, freqs.values()))

def triplet_method(ts, simplify=True):
    """Apply the triplet method (discussed in the blog post) to binary sequence `ts`."""
    # Skip the last few digits if the sequence is not a multiple of
    # three
    n_triples = int(len(ts)/3)
    final_ts = []
    for i in range(0, n_triples):
        triple = ts[i*3:(i+1)*3]
        if asstring(diff(triple)) in ["00", "11"]:
            continue
        if simplify:
            final_ts.append(1 if asstring(triple) in ["110", "011"] else 0)
        else:
            final_ts.append(1 if asstring(triple) in ["110", "001"] else 0)
    return final_ts


def triplet_generate(n, switch_prob=.5):
    """Generate a sequence of length `n` using the triplet method.

    Rather than applying the triplet method to an existing binary sequence,
    generate values for a binary sequence until we have one of length `n`.

    We use a cache (with a large cache size) as an easy way to avoid
    the criticism that the underlying sequence does not truly have the
    specified switch probability because short sequences are being
    generated and concatenated, which would no longer share those
    properties.
    """
    CACHE_SIZE = 900
    ts = []
    while len(ts)<n:
        cache = human_random(CACHE_SIZE, switch_prob)
        ts.extend(triplet_method(cache))
    return ts[0:n]

if __name__ == "__main__":
    # CREATE THE FIRST FIGURE
    ps = [i/100.0 for i in range(0, 100)]
    n_diffs = [0, 1, 2, 4, 8, 16, 32, 64]
    sns.set_palette(sns.cubehelix_palette(len(n_diffs)))
    sns.set_context("poster", font_scale=1.5)
    sns.set_style("white")
    for n_diff in n_diffs:
        nthdiffmeans_all = []
        for i in range(0, 5):
            nthdiffmeans = [mean(nthdiff(human_random(2000, p), n_diff)) for p in ps]
            nthdiffmeans_all.append(nthdiffmeans)
        
        plt.errorbar(ps, numpy.mean(nthdiffmeans_all, axis=0), scipy.stats.sem(nthdiffmeans_all, axis=0), label=ordinal(n_diff)+" difference")
    
    plt.xlabel("Switch probability")
    plt.ylabel("n'th difference mean")
    plt.legend(loc='upper left', fontsize='x-small')
    plt.savefig("nthdiffmeans-2powers.eps")
    sns.despine()
    plt.show()
    
    
    # CREATE THE SECOND FIGURE
    ps = [i/100.0 for i in range(0, 100)]
    n_diffs = [0, 1, 2, 3, 5, 9, 17, 33, 65]
    sns.set_palette(sns.cubehelix_palette(len(n_diffs)))
    sns.set_context("poster", font_scale=1.5)
    sns.set_style("white")
    for n_diff in n_diffs:
        nthdiffmeans_all = []
        for i in range(0, 5):
            nthdiffmeans = [mean(nthdiff(human_random(2000, p), n_diff)) for p in ps]
            nthdiffmeans_all.append(nthdiffmeans)
        
        plt.errorbar(ps, numpy.mean(nthdiffmeans_all, axis=0), scipy.stats.sem(nthdiffmeans_all, axis=0), label=ordinal(n_diff)+" difference")
    
    plt.xlabel("Switch probability")
    plt.ylabel("n'th difference mean")
    plt.legend(loc='upper left', fontsize='x-small')
    plt.savefig("nthdiffmeans-2powers-plus1.eps")
    sns.despine()
    plt.show()

    # CREATE THE THIRD FIGURE
    ps = [i/100.0 for i in range(3, 97)]
    n_diffs = [0, 1, 2, 3, 4, 8, 9, 16, 17, 32]
    sns.set_palette(sns.cubehelix_palette(len(n_diffs)))
    sns.set_context("poster", font_scale=1.5)
    sns.set_style("white")
    for n_diff in n_diffs:
        nthdiffmeans_all = []
        for i in range(0, 5):
            nthdiffmeans = [mean(nthdiff(triplet_method(human_random(20000, p)), n_diff)) for p in ps]
            nthdiffmeans_all.append(nthdiffmeans)
        
        plt.errorbar(ps, numpy.mean(nthdiffmeans_all, axis=0), scipy.stats.sem(nthdiffmeans_all, axis=0), label=ordinal(n_diff)+" difference")
    
    plt.xlabel("Switch probability")
    plt.ylabel("n'th difference mean")
    legend = plt.legend(loc='upper left', fontsize='x-small', frameon=True, fancybox=True)
    legend.get_frame().set_alpha(0.5)
    plt.savefig("nthdiffmeans-2powers-plus1-triplet.eps")
    sns.despine()
    plt.show()

    # CREATE THE FOURTH FIGURE
    n_entropies = [1, 2, 3, 4, 5, 6, 7, 8]
    n_diffs = [4, 8, 16, 32]
    n_diffs_p1 = [3, 5, 9, 17, 33]
    pal1 = sns.cubehelix_palette(len(n_diffs), start=0, dark=.4, light=.8)
    sns.set_context("poster", font_scale=1.5)
    sns.set_style("white")
    nth_entropies_all = []
    for i in range(0, 3):
        seq = human_random(20000, .8)
        nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
        nth_entropies_all.append(nth_entropies)
    plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label="Human-like", c="k")
    nth_entropies_all = []
    for i in range(0, 3):
        seq = triplet_generate(20000, .8)
        nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
        nth_entropies_all.append(nth_entropies)
    plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label="Triplet method", c="g")
    nth_entropies_all = []
    for i in range(0, 3):
        seq = human_random(20000, .5)
        nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
        nth_entropies_all.append(nth_entropies)
    plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label="True random", c="r", linestyle="--")
    nth_entropies_all = []
    for i in range(0, 3):
        seq = nthdiff(human_random(20000, .8), 1)
        nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
        nth_entropies_all.append(nth_entropies)
    plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label="1st difference", c=[150/255, 50/255, 200/255])
    nth_entropies_all = []
    for i in range(0, 3):
        seq = nthdiff(human_random(20000, .8), 2)
        nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
        nth_entropies_all.append(nth_entropies)
    plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label="2nd difference", c=[200/255, 100/255, 250/255])
    for j,n_diff in enumerate(n_diffs):
        nth_entropies_all = []
        for i in range(0, 3):
            seq = nthdiff(human_random(20000, .8), n_diff)
            nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
            nth_entropies_all.append(nth_entropies)
        plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label=ordinal(n_diff)+" difference", c=pal1[j])
    pal2 = sns.cubehelix_palette(len(n_diffs_p1), start=2, dark=.4, light=.8)
    sns.set_context("poster", font_scale=1.5)
    sns.set_style("white")
    for j,n_diff in enumerate(n_diffs_p1):
        nth_entropies_all = []
        for i in range(0, 3):
            seq = nthdiff(human_random(20000, .8), n_diff)
            nth_entropies = [nthentropy(seq, e)/e for e in n_entropies]
            nth_entropies_all.append(nth_entropies)
        plt.errorbar(n_entropies, numpy.mean(nth_entropies_all, axis=0), scipy.stats.sem(nth_entropies_all, axis=0), label=ordinal(n_diff)+" difference", c=pal2[j])
    
    plt.xlabel("n'th entropy")
    plt.ylabel("Normalized entropy")
    box = plt.gca().get_position()
    plt.gca().set_position([box.x0, box.y0, box.width * 0.8, box.height])
    legend = plt.legend(loc='upper left', fontsize='x-small', frameon=True, fancybox=True, bbox_to_anchor=(1, 0.92))
    legend.get_frame().set_alpha(0.5)
    plt.savefig("binary-sequence-entropy.eps")
    sns.despine()
    plt.show()
