# Copyright 2017 Max Shinn
# Available under the GPLv3
# http://blog.maxshinnpotential.com/2017/11/05/how-you-should-be-shuffling-cards.html

import random
import collections
import functools # For file caching
import dill # For file caching
import os # For file caching
# Cards are in the format (suit, number) where ace == 1, jack == 11,
# queen == 12, king == 13 and suits are 0-3.
SUITS = list(range(0, 4))
RANKS = list(range(1, 14))
DECK = [(suit, rank) for suit in SUITS for rank in RANKS]

import joblib
file_cache = joblib.Memory(cachedir="cache", verbose=0)

def get_suit_pattern(hand):
    hand_suit = [s for s,r in hand]
    return tuple(sorted((hand_suit.count(0), hand_suit.count(1), hand_suit.count(2), hand_suit.count(3))))

@file_cache.cache
def p_suit_distribution(hand_size, niter=1e6):
    """Given that a hand consists of `hand_size` cards, calculate the
    probability of observing a particular distribution of suits."""
    sorts = {}
    for i in range(0, int(niter)):
        hand = random.sample(DECK, hand_size)
        s = get_suit_pattern(hand)
        if s not in sorts.keys():
            sorts[s] = 0
        sorts[s] += 1
    for k,v in sorts.items():
        sorts[k] = v/niter
    return sorts

def get_rank_pattern(hand):
    hand_rank = [r for s,r in hand]
    return tuple(sorted(hand_rank.count(n) for n in RANKS))

@file_cache.cache
def p_rank_distribution(hand_size, niter=1e6):
    sorts = {}
    for i in range(0, int(niter)):
        hand = random.sample(DECK, hand_size)
        s = get_rank_pattern(hand)
        if s not in sorts.keys():
            sorts[s] = 0
        sorts[s] += 1
    for k,v in sorts.items():
        sorts[k] = v/niter
    return sorts

def get_cluster_pattern(hand):
    hand_rank = [r for s,r in hand]
    cluster_sizes = []
    cur_cluster_size = 1
    cur_cluster_rank = hand_rank[0]
    for c in hand_rank[1:]:
        if abs(c-cur_cluster_rank) <= 1:
            cur_cluster_rank = c
            cur_cluster_size += 1
        else:
            cluster_sizes.append(cur_cluster_size)
            cur_cluster_size = 1
            cur_cluster_rank = c
    cluster_sizes.append(cur_cluster_size)
    return tuple(sorted(cluster_sizes))

@file_cache.cache
def p_cluster_distribution(hand_size, niter=1e6):
    clusters = {}
    for i in range(0, int(niter)):
        hand = sorted(random.sample(DECK, hand_size))
        sizes_key = get_cluster_pattern(hand)
        if sizes_key not in clusters.keys():
            clusters[sizes_key] = 0
        clusters[sizes_key] += 1
    for k,v in clusters.items():
        clusters[k] = v/niter
    return clusters

@file_cache.cache
def p_suit_cluster_distribution(hand_size, niter=1e6):
    dist = {}
    for i in range(0, int(niter)):
        hand = sorted(random.sample(DECK, hand_size))
        suit_key = get_suit_pattern(hand)
        cluster_key = get_cluster_pattern(hand)
        key = (suit_key, cluster_key)
        if key not in dist.keys():
            dist[key] = 0
        dist[key] += 1
    for k,v in dist.items():
        dist[k] = v/niter
    return dist

@file_cache.cache
def p_suit_rank_cluster_distribution(hand_size, niter=1e6):
    dist = {}
    for i in range(0, int(niter)):
        hand = sorted(random.sample(DECK, hand_size))
        suit_key = get_suit_pattern(hand)
        rank_key = get_rank_pattern(hand)
        cluster_key = get_cluster_pattern(hand)
        key = (suit_key, rank_key, cluster_key)
        if key not in dist.keys():
            dist[key] = 0
        dist[key] += 1
    for k,v in dist.items():
        dist[k] = v/niter
    return dist

import math
import numpy as np

def join_lists(args):
    """Join the lists in `args` together to form one list."""
    l = []
    for a in args:
        l.extend(a)
    return l

def transpose(M):
    """Transpose a matrix `M`."""
    assert all(len(l) == len(M[0]) for l in M), "Sub-lists different length"
    MT = []
    for i in range(0, len(M[0])):
        MT.append([l[i] for l in M])
    return MT

def iterate_shuffle(deck, method, niter):
    """Perform the shuffle `method` on `deck` `niter` times."""
    thisdeck = deck
    for _ in range(0, niter):
        thisdeck = method(thisdeck)
    return thisdeck

def cut_shuffle(deck):
    """Cut the deck once. Don't allow identity cuts."""
    print("In cut" + str(deck))
    i = random.randint(1, len(deck)-2)
    return deck[i:] + deck[0:i]

def pile_shuffle(deck, npiles):
    """Deal into `npiles` piles, and then combine them."""
    piles = [deck[i::npiles] for i in range(0, npiles)]
    return join_lists(piles)

def pile_shuffle_random_pickup(deck, npiles):
    """Like pile_shuffle, but pick up the piles in a random order"""
    piles = [deck[i::npiles] for i in range(0, npiles)]
    random.shuffle(piles)
    return join_lists(piles)

def pile_shuffle_random_distribute(deck, npiles):
    """Like a pile shuffle, but put each card into a random pile.
    Always ensure that the absolute value between deck lengths is at
    most 1."""
    os = [random.sample(list(range(0, npiles)), npiles) for _ in range(0, math.ceil(len(deck)/npiles))]
    o = join_lists(os)
    piles = [[] for _ in range(0, npiles)]
    for p,c in zip(o, deck):
        piles[p].append(c)
    return join_lists(piles)

def pile_shuffle_fully_random_distribute(deck, npiles):
    """Like a pile shuffle, but put each card into a random pile.  Do
    not ensure that the piles are the same size."""
    piles = [[] for _ in range(0, npiles)]
    for c in deck:
        p = np.random.randint(0, npiles)
        piles[p].append(c)
    return join_lists(piles)

def integrate_binary(ts, start=0):
    """Return  the first integral sequence of the binary sequence `ts`.

    In other words, given a diff sequence, construct a binary sequence
    that would have that diff.  The first digit should be `start`,
    which should have a value of 0 or 1.
    """
    outputts = [start]
    for e in ts:
        outputts.append(int(bool(int(e)) != bool(int(outputts[-1])))) # XOR
    return outputts

def riffle_shuffle(deck, p_switch):
    """A riffle shuffle, with a probability of two cards coming from
    the same deck being (1-`p_switch`)."""
    sw = [int(random.random()<p_switch) for _ in range(0, len(deck)-1)]
    split = integrate_binary(sw, random.randint(0, 1))
    i_half = int(len(deck)/2)
    lh_half = list(reversed(deck[0:i_half]))
    rh_half = list(reversed(deck[i_half:]))
    shuffled = []
    for s in split:
        if len(rh_half) == 0:
            shuffled.extend(list(reversed(lh_half)))
            break
        elif len(lh_half) == 0:
            shuffled.extend(list(reversed(rh_half)))
            break
        if s == 0:
            shuffled.append(rh_half.pop())
        elif s == 1:
            shuffled.append(lh_half.pop())
    return shuffled

def riffle_gsr_shuffle(deck):
    """A riffle shuffle according to the Gilbert-Shannon-Reeds model"""
    split_pos = np.random.binomial(len(deck), .5)
    lh_half = deck[0:split_pos]
    rh_half = deck[split_pos:]
    shuffled = []
    while len(lh_half) + len(rh_half) > 0:
        p_rh = len(rh_half)/(len(lh_half) + len(rh_half))
        shuffled.append(rh_half.pop() if random.random() < p_rh else lh_half.pop())
    shuffled.reverse()
    return shuffled

def overhand_shuffle(deck, mean_nsplits):
    """An overhand shuffle chooses a random number of split points
    (with mean `mean_nsplits`) and the divides the deck into that many
    splits.  Then it combines them in reverse order."""
    nsplits = np.random.binomial(len(deck), mean_nsplits/len(deck))
    splitpoints = random.sample(list(range(1, len(deck)-1)), nsplits)
    splitpoints.extend([0, len(deck)])
    splitpoints.sort()
    decks = [deck[i:j] for i,j in zip(splitpoints[0:], splitpoints[1:])]
    decks.reverse()
    return join_lists(decks)

# Default shuffling methods
from collections import OrderedDict

methods = OrderedDict()
methods['riffle_me'] = lambda x : riffle_shuffle(x, .45)
methods['riffle_expert'] = lambda x : riffle_shuffle(x, .8)
methods['riffle_bad'] = lambda x : riffle_shuffle(x, .2)
methods['riffle_gsr'] = lambda x : riffle_gsr_shuffle(x)
methods['overhand'] = lambda x : overhand_shuffle(x, 5)
methods['overhand_many'] = lambda x : overhand_shuffle(x, 8)
methods['overhand_few'] = lambda x : overhand_shuffle(x, 3)

methods['pile_1'] = lambda x : pile_shuffle(x, 1)
methods['pile_2'] = lambda x : pile_shuffle(x, 2)
methods['pile_3'] = lambda x : pile_shuffle(x, 3)
methods['pile_4'] = lambda x : pile_shuffle(x, 4)
methods['pile_5'] = lambda x : pile_shuffle(x, 5)
methods['pile_6'] = lambda x : pile_shuffle(x, 6)
methods['pile_7'] = lambda x : pile_shuffle(x, 7)
methods['pile_8'] = lambda x : pile_shuffle(x, 8)

methods['pile_1_rp'] = lambda x : pile_shuffle_random_pickup(x, 1)
methods['pile_2_rp'] = lambda x : pile_shuffle_random_pickup(x, 2)
methods['pile_3_rp'] = lambda x : pile_shuffle_random_pickup(x, 3)
methods['pile_4_rp'] = lambda x : pile_shuffle_random_pickup(x, 4)
methods['pile_5_rp'] = lambda x : pile_shuffle_random_pickup(x, 5)
methods['pile_6_rp'] = lambda x : pile_shuffle_random_pickup(x, 6)
methods['pile_7_rp'] = lambda x : pile_shuffle_random_pickup(x, 7)
methods['pile_8_rp'] = lambda x : pile_shuffle_random_pickup(x, 8)

methods['pile_1_rd'] = lambda x : pile_shuffle_random_distribute(x, 1)
methods['pile_2_rd'] = lambda x : pile_shuffle_random_distribute(x, 2)
methods['pile_3_rd'] = lambda x : pile_shuffle_random_distribute(x, 3)
methods['pile_4_rd'] = lambda x : pile_shuffle_random_distribute(x, 4)
methods['pile_5_rd'] = lambda x : pile_shuffle_random_distribute(x, 5)
methods['pile_6_rd'] = lambda x : pile_shuffle_random_distribute(x, 6)
methods['pile_7_rd'] = lambda x : pile_shuffle_random_distribute(x, 7)
methods['pile_8_rd'] = lambda x : pile_shuffle_random_distribute(x, 8)

SUITS = list(range(0, 4))
RANKS = list(range(1, 14))
RED_SUITS = [1, 3]
BLACK_SUITS = [0, 2]
DECK = [(suit, rank) for suit in SUITS for rank in RANKS]

decks = OrderedDict()
decks['Shuffled deck'] = lambda : random.sample(DECK, 52)
decks['Sorted deck (by suit)'] = lambda : DECK
decks['Sorted deck (by rank)'] = lambda : [(suit, rank) for rank in RANKS for suit in SUITS]

# Defining deck patterns which originate from different games

# Groups of 4 in  a row by suit
def go_fish_4():
    return join_lists([[(suit, rank) for suit in random.sample(SUITS, 4)]
                                     for rank in random.sample(RANKS, 13)])
assert sorted(DECK) == sorted(go_fish_4())
decks['Go Fish (four-card)'] = go_fish_4

# Groups of 2 in a row by suit
def go_fish_2():
    d = []
    gf4 = go_fish_4()
    for i in range(0, 52, 2):
        d.append(gf4[i:i+2])
    random.shuffle(d)
    return join_lists(d)
    
assert sorted(DECK) == sorted(go_fish_2())
decks['Go Fish (two-card)'] = go_fish_2

# Where only the color must be correct
def go_fish_color():
    red = [[(suit, rank) for suit in RED_SUITS] for rank in RANKS]
    black = [[(suit, rank) for suit in BLACK_SUITS] for rank in RANKS]
    d = red + black
    random.shuffle(d)
    return join_lists(d)

assert sorted(DECK) == sorted(go_fish_color())
decks['Go Fish (color variant)'] = go_fish_color

def kings_corners():
    l = [[] for _ in range(0, len(SUITS))]
    for i,rank in enumerate(RANKS):
        if i % 2 == 0:
            s = random.sample(RED_SUITS, 2) + random.sample(BLACK_SUITS, 2)
        else:
            s = random.sample(BLACK_SUITS, 2) + random.sample(RED_SUITS, 2)
        for i in range(0, len(SUITS)):
            l[i].append((s[i], rank))
    random.shuffle(l)
    return join_lists(l)

assert sorted(DECK) == sorted(kings_corners())
decks['Kings Corners'] = kings_corners

def durak():
    remaining_ranks = RANKS.copy()
    random.shuffle(remaining_ranks)
    subdeck_ranks = []
    while remaining_ranks:
        pilesize = np.random.poisson(1)
        if pilesize > len(remaining_ranks):
            pilesize = len(remaining_ranks)
        if pilesize == 0:
            continue
        subdeck_ranks.append(remaining_ranks[0:pilesize])
        remaining_ranks = remaining_ranks[pilesize:]
    cards = []
    for rnks in subdeck_ranks:
        thispile = [(st, rnk) for rnk in rnks for st in SUITS]
        random.shuffle(thispile)
        cards += thispile
    return cards

assert sorted(DECK) == sorted(durak())
decks['Durak'] = durak

# Different types of deals
def deal_naive(deck, players=4, handsize=6):
    return deck[0:handsize]

def deal_basic(deck, players=4, handsize=6):
    return deck[0:handsize*players:players]
