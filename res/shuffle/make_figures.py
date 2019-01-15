# Copyright 2017 Max Shinn
# Available under the GPLv3
# http://blog.maxshinnpotential.com/2017/11/05/how-you-should-be-shuffling-cards.html

from cards import *
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from statistics import median

sns.set_context("talk", font_scale=1.0)
sns.set_style("whitegrid")
sns.set_palette(sns.color_palette("hls", len(decks)))

HANDSIZE = 6

# Simulate the joint distributions of expected suit, rank, and
# clustering.
#suit_dist = p_suit_distribution(HANDSIZE, 1e7)
#rank_dist = p_rank_distribution(HANDSIZE, 1e7)
#cluster_dist = p_cluster_distribution(HANDSIZE, 1e7)
#suit_cluster_dist = p_suit_cluster_distribution(HANDSIZE, 1e7)
suit_rank_cluster_dist = defaultdict(lambda : 0, p_suit_rank_cluster_distribution(HANDSIZE, 1e7))

def test(deck, deal=deal_basic, players=4):
    """Deal a hand from deck `deck` using dealing function `deal` to
    `players` players and find the joint probability of the hand."""
    suit_pattern = get_suit_pattern(deal(deck, handsize=HANDSIZE, players=players))
    rank_pattern = get_rank_pattern(deal(deck, handsize=HANDSIZE, players=players))
    cluster_pattern = get_cluster_pattern(deal(deck, handsize=HANDSIZE, players=players))
    return suit_rank_cluster_dist[(suit_pattern, rank_pattern, cluster_pattern)]


#  ___ _  __  __ _          _         __  __ _
# | _ (_)/ _|/ _| |___   __| |_ _  _ / _|/ _| |___
# |   / |  _|  _| / -_) (_-< ' \ || |  _|  _| / -_)
# |_|_\_|_| |_| |_\___| /__/_||_\_,_|_| |_| |_\___|



def plot_shuffles(method, n_shuffles=10, ntrials=100):
    """Plot the shuffling method's accuracy for all decks.

    `method` is the shuffling method's name, from the "methods"
    dictionary.

    `n_shuffles` is the maximum number of shuffle iterations, i.e. 3
    riffle shuffles, 4 riffle shuffles, etc.

    `ntrials` is the number of times to compute this quantity before
    taking the median.
    """
    method = methods[method]
    for name,deck in decks.items():
        print("Testing %s" % name)
        shuffle_ns = list(range(0, n_shuffles))
        prob = []
        for n in shuffle_ns:
            thisprob = []
            for _ in range(0, ntrials):
                thisprob.append(math.log10(1e-10+test(iterate_shuffle(deck(), method, n), deal=deal_naive)))
            prob.append(sum(thisprob))
        plt.plot(shuffle_ns, prob, label=name)

plt.figure(figsize=(8,6))
plt.subplot(2,2,1)
plot_shuffles('riffle_me')
plt.title("My riffle shuffle")

plt.subplot(2,2,2)
plot_shuffles('riffle_gsr')
plt.title("GSR riffle shuffle")

plt.subplot(2,2,3)
plot_shuffles('riffle_bad', 15)
plt.title("Novice riffle shuffle")

plt.subplot(2,2,4)
plot_shuffles('riffle_expert')
plt.title("Expert riffle shuffle")
legtext = plt.gca().get_legend_handles_labels()

plt.gcf().text(0.5, 0.04, 'Number of riffle shuffles', ha='center')
plt.gcf().text(0.04, 0.5, "Likelihood (higher is more random)", va='center', rotation='vertical')
plt.subplot(2,2,3)
plt.xlabel(".", alpha=1)
plt.ylabel(".", alpha=1)
plt.tight_layout()
plt.savefig("riffle.png")
plt.show(block=False)

plt.figure(figsize=(3,3))
plt.figlegend(*legtext, loc="center")
plt.savefig("legend.png")
plt.show(block=False)



#   ___              _                 _      _         __  __ _
#  / _ \__ _____ _ _| |_  __ _ _ _  __| |  __| |_ _  _ / _|/ _| |___
# | (_) \ V / -_) '_| ' \/ _` | ' \/ _` | (_-< ' \ || |  _|  _| / -_)
#  \___/ \_/\___|_| |_||_\__,_|_||_\__,_| /__/_||_\_,_|_| |_| |_\___|




plt.figure(figsize=(8,6))
plt.subplot(2,1,1)
plot_shuffles('overhand', 50)
plt.title("Overhand shuffle, average number of cuts")

plt.subplot(2,2,3)
plot_shuffles('overhand_many', 50)
plt.title("Many cuts")

plt.subplot(2,2,4)
plot_shuffles('overhand_few', 50)
plt.title("Few cuts")

plt.gcf().text(0.5, 0.04, 'Number of overhand shuffles', ha='center')
plt.gcf().text(0.04, 0.5, "Likelihood (higher is more random)", va='center', rotation='vertical')
plt.subplot(2,2,3)
plt.xlabel(".", alpha=1)
plt.ylabel(".", alpha=1)
plt.tight_layout()
plt.savefig("overhand.png")
plt.show(block=False)


#  ___ _ _          _         __  __ _
# | _ (_) |___   __| |_ _  _ / _|/ _| |___
# |  _/ | / -_) (_-< ' \ || |  _|  _| / -_)
# |_| |_|_\___| /__/_||_\_,_|_| |_| |_\___|



def plot_pile_shuffles(randomize="none", ntrials=100, deal=deal_naive, players=4):
    """Plot pile shuffle accuracy for various numbers of piles.

    `ranzomize` can either be "none", "distribute", "fully", or
    "pickup" to correspond to randomizing how the cards are
    distributed (e.g. first card in pile 3, second card in pile 2
    third card in pile 2, fourth card in pile 1) or else how they are
    picked up.
    
    `ntrials` is the number of times to compute this quantity before
    taking the median.

    `players` is the number of players to deal for.  Only applies to
    `deal_basic`.

    `deal` is either `deal_naive` or `deal_basic`.
    """
    for name,deck in decks.items():
        print("Testing %s" % name)
        pile_ns = list(range(1, 15))
        prob = []
        for n in pile_ns:
            if randomize == "none":
                method = lambda x : pile_shuffle(x, n)
            elif randomize == "pickup":
                method = lambda x : pile_shuffle_random_pickup(x, n)
            elif randomize == "distribute":
                method = lambda x : pile_shuffle_random_distribute(x, n)
            elif randomize == "fully":
                method = lambda x : pile_shuffle_fully_random_distribute(x, n)
            else:
                raise ValueError("Invalid pile randomization type")
            thisprob = []
            for _ in range(0, ntrials):
                thisprob.append(math.log10(1e-10+test(method(deck()), deal=deal, players=players)))
            prob.append(sum(thisprob))
        plt.plot(pile_ns, prob, label=name)
    plt.axis([1, 14, None, None])

plt.figure(figsize=(8,6))
plt.subplot(2,2,1)
plot_pile_shuffles()
plt.title("No randomization")

plt.subplot(2,2,2)
plot_pile_shuffles("pickup")
plt.title("Random pickup")

plt.subplot(2,2,3)
plot_pile_shuffles("distribute")
plt.title("Random piles, equal sized")

plt.subplot(2,2,4)
plot_pile_shuffles("fully")
plt.title("Random piles, unequal sized")

plt.gcf().text(0.5, 0.04, 'Number of piles', ha='center')
plt.gcf().text(0.04, 0.5, "Likelihood (higher is more random)", va='center', rotation='vertical')
plt.subplot(2,2,3)
plt.xlabel(".", alpha=1)
plt.ylabel(".", alpha=1)
plt.tight_layout()
plt.savefig("piles.png")
plt.show(block=False)



#   ___           _    _           _   _
#  / __|___ _ __ | |__(_)_ _  __ _| |_(_)___ _ _  ___
# | (__/ _ \ '  \| '_ \ | ' \/ _` |  _| / _ \ ' \(_-<
#  \___\___/_|_|_|_.__/_|_||_\__,_|\__|_\___/_||_/__/


def compose_methods(shuffle_types, shuffle_functions):
    """Combine multiple shuffle functions into one.

    `Shuffle_types` should be a list of ints, indexing
    `shuffle_functions`.  `shuffle_functions` is a list of functions
    which take one argument, the deck, and return a shuffled deck.
    """
    def shuffle_composite_function(deck):
        deck = deck.copy()
        for t in shuffle_types:
            deck = shuffle_functions[t](deck)
        return deck
    return shuffle_composite_function

def plot_riffle_overhand(shuffles, ntrials=100, deal=deal_naive, players=4):
    """Plot a composite of riffle shuffles and overhand shuffles.  

    `shuffles` is a list of 0's and 1's.  0 means use a riffle
    shuffle, and 1 means use an overhand shuffle.  These shuffles will
    be performed in sequence, and plotted at each step.
    """
    for name,deck in decks.items():
        prob = []
        for i in range(0, len(shuffles)):
            method = compose_methods(shuffles[0:i], [methods['riffle_gsr'], methods['overhand']])
            thisprob = []
            for _ in range(0, ntrials):
                thisprob.append(math.log10(1e-10+test(method(deck()), deal=deal, players=players)))
            prob.append(sum(thisprob))
        plt.plot(range(0, len(shuffles)), prob, label=name)


# You can play with these if you want, but they just look like shifted
# versions of the riffle shuffle.  For example, for a riffle, then an
# overhand, and then a riffle:
#
# plot_riffle_overhand([0, 1, 0, 0])
# plt.show()

