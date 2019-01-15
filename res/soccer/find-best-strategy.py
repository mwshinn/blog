import numpy, scipy
from scipy.stats import binom
import matplotlib.pyplot as plt
import seaborn as sns

COST_PER_SHOT = .01
TOTAL_WINNINGS = 100
BET_A = (2, 3)
BET_B = (5, 8)

# Probability of winning if you need to make `needed` shots out of
# `shots` total.
def prob_winning(needed, shots, p_success):
    return 1-binom.cdf(p=p_success, n=shots, k=needed-1)

# The parameters of the question are: 2/3, or 5/8.  Assume that for
# someone who is very talented, bet B is easier than bet A.
bet_a = lambda p : prob_winning(needed=BET_A[0], shots=BET_A[1], p_success=p)
bet_b = lambda p : prob_winning(needed=BET_B[0], shots=BET_B[1], p_success=p)

# Always plot with resolution of 1/100
x_domain = [i/100 for i in range(0, 101)]

# Figure out when you should take bet A and when you should take bet B.
bets_equal = lambda p : bet_a(p) - bet_b(p)
equivalence_point = scipy.optimize.fsolve(bets_equal, .5)[0]

# Now, compute the maximum possible increase in expected value you can
# get from choosing A over B or B over A.
o1 = scipy.optimize.fmin(lambda p : -bets_equal(p), .1)[0]
o2 = scipy.optimize.fmin(lambda p : -bets_equal(p), .9)[0]
o3 = scipy.optimize.fmin(bets_equal, .1)[0]
o4 = scipy.optimize.fmin(bets_equal, .9)[0]
oa = o1 if o1 > .001 else o2
ob = o3 if o3 > .001 else o4
if abs(bets_equal(oa)) < abs(bets_equal(ob)):
    max_p = oa
    max_gain = abs(bets_equal(oa))*TOTAL_WINNINGS
else:
    max_p = ob
    max_gain = abs(bets_equal(ob))*TOTAL_WINNINGS

# It is never a good idea to take more than this many shots
max_shots = int(numpy.ceil(max_gain/COST_PER_SHOT))

print("Equivalence point: %.4f, max gain: %.4f, shots upper bound: %i" % (equivalence_point, max_gain, max_shots))

# Visualize the two bets
sns.set_context("poster", font_scale=1.5)
sns.set_style("white")
plt.plot(x_domain, [TOTAL_WINNINGS*v for v in map(bet_a, x_domain)])
plt.plot(x_domain, [TOTAL_WINNINGS*v for v in map(bet_b, x_domain)])
plt.xlabel("Probability of making the shot")
plt.ylabel("Expected payoff of each bet")
plt.legend(["Game (A)", "Game (B)"], loc=2)
sns.despine()
plt.savefig("winning_prob_binom.eps")
plt.show()

while True:
    resp = input("Continue? (y/n): ")
    if resp == "y":
        break
    if resp == "n":
        exit()

# Divide up the space of possible p's into segments so that we can
# numerically estimate the integral using trapezoids
partition = numpy.linspace(0, 1, 101)

# Estimate the expected value of taking a bet at each state.  c =
# number of practice shots you make, t = total number of practice
# shots you take, bet = tuple, where the first is the number you need
# in the bet and the second is the total you must get.
def estimate_V(c, t, bet):
    # We want the probability that p_0 is within some segment of
    # `partition`.  We integrate across it using the cdf.
    betacdfs = scipy.stats.beta.cdf(partition, a=c+1, b=t-c+1)
    # The payoff for each probability at the partition boundary
    Abounds = TOTAL_WINNINGS*prob_winning(p_success=partition, needed=bet[0], shots=bet[1])
    # Estimate the total for each partition bin by averaging the
    # boundaries, and multiplying by the probability of getting it.
    Apartition = [.5*(Abounds[i] + Abounds[i+1])*(betacdfs[i+1]-betacdfs[i]) for i in range(0, len(Abounds)-1)]
    return sum(Apartition) - t*COST_PER_SHOT

def estimate_VA(c, t):
    return estimate_V(c, t, bet=BET_A)

def estimate_VB(c, t):
    return estimate_V(c, t, bet=BET_B)

# If we were to make a choice of one of the two bets at some point,
# which bet would be best?
def VA_or_VB(c, t):
    return "A" if estimate_VA(c, t) > estimate_VB(c, t) else "B"

# If we were to make a choice of one of the two bets at some point,
# what would be the expected payoff?
def stopping_value(c, t):
    return max(estimate_VA(c, t), estimate_VB(c, t))


# Upper triangular matrix for which choice to make and the value of that choice.
bestchoiceval = numpy.zeros((max_shots+1, max_shots+1))
bestchoice = numpy.empty((max_shots+1, max_shots+1), dtype="U1") # "A",
# "B", or "S" We know that after you have taken max_shots shots you
# should always have chosen.
for c in range(0, max_shots+1):
    bestchoice[c,max_shots] = VA_or_VB(c, max_shots)
    bestchoiceval[c,max_shots] = stopping_value(c, max_shots)

for n in range(max_shots-1, -1, -1):
    print(n)
    for c in range(0, n+1):
        # If we will choose the same thing no matter what the outcome
        # of the shot, don't take the shot.  (No, you DON'T miss all
        # the shots you don't take.)
        if bestchoice[c,n+1] == bestchoice[c+1,n+1] and bestchoice[c,n+1] in ["A", "B"]:
            bestchoice[c,n] = bestchoice[c,n+1]
            bestchoiceval[c,n] = stopping_value(c, n)
        else:
            # Calculate the expected value of taking the shot vs
            # staying.  Estimate the expected value assuming a
            # probability of making each shot equal to your current
            # sample probability.
            if n > 0:
                shootval = c/n*bestchoiceval[c+1,n+1] + (1-(c/n))*bestchoiceval[c,n+1] - COST_PER_SHOT
            else:
                shootval = numpy.inf
            if shootval > stopping_value(c, n):
                bestchoice[c,n] = "S"
                bestchoiceval[c,n] = shootval
            else:
                bestchoice[c,n] = VA_or_VB(c, n)
                bestchoiceval[c,n] = stopping_value(c, n)

numpy.savetxt("bestchoice.csv", bestchoice, delimiter=",", fmt="%s")

# Print a pretty decision tree
getcolor = numpy.vectorize(lambda x : 0 if x == "" else 1 if x == "A" else 2 if x == "B" else 3)

plt.imshow(getcolor(bestchoice), origin="lower", interpolation='none', cmap=colors.ListedColormap(["white"] + sns.color_palette(n_colors=3)))
plt.xlabel("Total number of shots")
plt.ylabel("Number of successes")
sns.despine(left=True, bottom=True)
plt.savefig("decision-tree.eps")
plt.show()

plt.imshow(getcolor(bestchoice)[0:100,0:100], origin="lower", interpolation='none', cmap=colors.ListedColormap(["white"] + sns.color_palette(n_colors=3)))
plt.xlabel("Total number of shots")
plt.ylabel("Number of successes")
sns.despine(left=True, bottom=True)
plt.savefig("decision-tree-zoomed.eps")
plt.show()
