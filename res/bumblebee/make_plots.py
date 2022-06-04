import numpy as np
import mido
import numpy as np
colours = ["#1b9e77", "#d95f02"]
f = mido.MidiFile("flight_melody.mid")
dat = [m for m in f if isinstance(m, mido.Message) and m.type == "note_on" and m.velocity > 0]
notes = [m.note for m in dat]
jumps = np.diff(notes)



def run_process(dist, n):
    vals = [0]
    for i in range(0, n):
        d = dist()
        v = vals[-1] + np.random.choice([-1,1]) * d
        vals.append(v)
    return vals

def run_process_2d(dist, n):
    vals = [[0,0]]
    for i in range(0, n):
        d = dist()
        a = np.random.uniform(0, np.pi*2)
        v = vals[-1] + np.asarray([np.cos(a), np.sin(a)]) * d
        vals.append(v)
    return np.asarray(vals)

def adjust_spines(ax, spines):
    for loc, spine in ax.spines.items():
        if loc in spines:
            spine.set_position(('outward', 10))  # outward by 10 points
        else:
            spine.set_color('none')  # don't draw spine

# Create 1D plot
np.random.seed(0)
plt.figure(figsize=(7,2.5))
plt.subplot(1,3,1)
plt.plot(run_process(lambda : scipy.stats.geom(.1).rvs(), 805), c=colours[0])
sns.despine()
plt.gca().set_xticks([])
plt.gca().set_yticks([])
plt.gca().set_xlabel("Time")
plt.gca().set_ylabel("Position / note value")
adjust_spines(plt.gca(), ["left", "bottom"])
plt.title("Geometric")
plt.subplot(1,3,2)
plt.plot(run_process(lambda : scipy.stats.zipf(1.99).rvs(), 805), c=colours[1])
sns.despine(left=True, ax=plt.gca())
plt.gca().set_xticks([])
plt.gca().set_yticks([])
plt.gca().set_xlabel("Time")
adjust_spines(plt.gca(), ["bottom"])
plt.gca().set_yticks([])
plt.title("Powerlaw")
plt.subplot(1,3,3)
plt.plot(notes, c='k')
sns.despine(left=True, ax=plt.gca())
plt.gca().set_xticks([])
plt.gca().set_yticks([])
plt.gca().set_xlabel("Time")
adjust_spines(plt.gca(), ["bottom"])
plt.title("Flight of the Bumblebee")
plt.tight_layout()

plt.savefig("random-processes-1d.png")
plt.show()

# Create 2D plot
np.random.seed(1)
plt.figure(figsize=(7,4))
plt.subplot(1,2,1)
trace = run_process_2d(lambda : scipy.stats.geom(.5).rvs(), 500)
plt.plot(trace[:,0], trace[:,1], c=colours[0])
plt.axis("off")
plt.title("Geometric")
plt.subplot(1,2,2)
trace = run_process_2d(lambda : scipy.stats.zipf(2.3).rvs(), 500)
plt.plot(trace[:,0], trace[:,1], c=colours[1])
plt.axis("off")
plt.title("Powerlaw")
plt.savefig("random-processes-2d.png")
plt.show()
