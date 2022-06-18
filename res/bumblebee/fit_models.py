import mido
import scipy.stats
import numpy as np
import scipy.optimize
import seaborn as sns
colours = ["#1b9e77", "#d95f02"]
f = mido.MidiFile("flight_melody.mid")
dat = [m for m in f if isinstance(m, mido.Message) and m.type == "note_on" and m.velocity > 0]
notes = [m.note for m in dat]
jumps = np.diff(notes)

fit = lambda dist, data,bounds : scipy.optimize.differential_evolution(lambda params : -np.sum(np.log(dist(*params).pmf(data))), bounds=bounds)

def plot_fit(name, loglike_geom, loglike_zipf, scale=100):
    logdiff = loglike_zipf - loglike_geom
    plt.figure(figsize=(7, 1.5))
    plt.barh([0], [logdiff], color=(colours[0] if logdiff<0 else colours[1]))
    plt.title("Geometric model                            Powerlaw model")
    plt.xlabel("How many times more likely")
    plt.axvline(0, c='k')
    plt.axis([-scale, scale, -.5, .5])
    plt.gca().xaxis.set_major_formatter(lambda x, pos: '=' if x == 0 else f"$10^{{{int(abs(x))}}}$")
    sns.despine(left=True)
    plt.gca().set_yticks([])
    plt.tight_layout()
    plt.savefig(name)
    plt.show()


fit_geom = fit(scipy.stats.geom, np.abs(jumps)[np.abs(jumps)!=0], [(0, 1)])
like_geom = np.sum(np.log10(scipy.stats.geom(*fit_geom.x).pmf(np.abs(jumps)[np.abs(jumps)!=0])))
fit_zipf = fit(scipy.stats.zipf, np.abs(jumps)[np.abs(jumps)!=0], [(0, 100)])
like_zipf = np.sum(np.log10(scipy.stats.zipf(*fit_zipf.x).pmf(np.abs(jumps)[np.abs(jumps)!=0])))

plot_fit("model-comparison.png", like_geom, like_zipf)
print(10**np.abs(like_geom-like_zipf))


jumps_nofourth = [j for j in jumps if j != 5]
fit_geom = fit(scipy.stats.geom, np.abs(jumps_nofourth)[np.abs(jumps_nofourth)!=0], [(0, 1)])
like_geom = np.sum(np.log10(scipy.stats.geom(*fit_geom.x).pmf(np.abs(jumps_nofourth)[np.abs(jumps_nofourth)!=0])))
fit_zipf = fit(scipy.stats.zipf, np.abs(jumps_nofourth)[np.abs(jumps_nofourth)!=0], [(0, 100)])
like_zipf = np.sum(np.log10(scipy.stats.zipf(*fit_zipf.x).pmf(np.abs(jumps_nofourth)[np.abs(jumps_nofourth)!=0])))

plot_fit("model-comparison-nofourth.png", like_geom, like_zipf)
print(10**np.abs(like_geom-like_zipf))



f = mido.MidiFile("gladiators_melody.mid")
dat = [m for m in f if isinstance(m, mido.Message) and m.type == "note_on" and m.velocity > 0]
notes = [m.note for m in dat]
jumps = np.diff(notes)

fit_geom = fit(scipy.stats.geom, np.abs(jumps)[np.abs(jumps)!=0], [(0, 1)])
like_geom = np.sum(np.log10(scipy.stats.geom(*fit_geom.x).pmf(np.abs(jumps)[np.abs(jumps)!=0])))
fit_zipf = fit(scipy.stats.zipf, np.abs(jumps)[np.abs(jumps)!=0], [(0, 100)])
like_zipf = np.sum(np.log10(scipy.stats.zipf(*fit_zipf.x).pmf(np.abs(jumps)[np.abs(jumps)!=0])))

plot_fit("model-comparison-gladiators.png", like_geom, like_zipf, scale=3)
print(10**np.abs(like_geom-like_zipf))




whole_tone_colours = ["#984ea3", "#a65628"]
f = mido.MidiFile("flight_melody.mid")
noteons = [m for m in f if isinstance(m, mido.Message) and m.type == "note_on"]
note_timings = np.round(np.cumsum([n.time for n in noteons])/.25, 1)
on_beats = (note_timings==note_timings.astype(int))
on_beat_notes = [n.note for n,t in zip(noteons,on_beats)if n.velocity > 0 and t]
on_beat_notes_times = [note_timings[i] for i,t in zip(range(0, len(noteons)),on_beats)if noteons[i].velocity > 0 and t]
on_beat_notes_scale = np.asarray(on_beat_notes) % 2
off_beats = (note_timings+.5==(note_timings+.5).astype(int))
off_beat_notes = [n.note for n,t in zip(noteons,off_beats)if n.velocity > 0 and t]
off_beat_notes_times = [note_timings[i] for i,t in zip(range(0, len(noteons)),off_beats)if noteons[i].velocity > 0 and t]
off_beat_notes_scale = np.asarray(off_beat_notes) % 2

plt.figure(figsize=(7,1.3))
plt.scatter(on_beat_notes_times/note_timings[-1]*f.length, on_beat_notes_scale, c=[whole_tone_colours[1] if v else whole_tone_colours[0] for v in on_beat_notes_scale], s=2)
plt.gca().set_yticks([0, 1])
plt.gca().set_yticklabels(["C♮ whole-tone scale", "D♭ whole-tone scale"])
plt.xlabel("Time (seconds)")
plt.gca().set_ylim(-.5, 1.5)
plt.gca().set_xlim(0, 110.5)
plt.gca().yaxis.set_ticks_position('none')
plt.title("On-beat whole-tone scale")
sns.despine(left=True)
plt.tight_layout()
plt.savefig("whole-tone-melody.png")
plt.show()

plt.figure(figsize=(7,1.3))
plt.scatter(off_beat_notes_times/note_timings[-1]*f.length, off_beat_notes_scale, c=[whole_tone_colours[1] if v else whole_tone_colours[0] for v in off_beat_notes_scale], s=2)
plt.gca().set_yticks([0, 1])
plt.gca().set_yticklabels(["C♮ whole-tone scale", "D♭ whole-tone scale"])
plt.xlabel("Time (seconds)")
plt.gca().set_ylim(-.5, 1.5)
plt.gca().set_xlim(0, 110.5)
plt.gca().yaxis.set_ticks_position('none')
plt.title(f"Off-beat whole-tone scale")
sns.despine(left=True)
plt.tight_layout()
plt.savefig("whole-tone-melody-off.png")
plt.show()




f = mido.MidiFile("gladiators_melody.mid")
noteons = [m for m in f if isinstance(m, mido.Message) and m.type == "note_on"]
note_timings = np.round(np.cumsum([n.time for n in noteons])/.5, 1)
on_beats = (note_timings==note_timings.astype(int))
on_beat_notes = [n.note for n,t in zip(noteons,on_beats)if n.velocity > 0 and t]
on_beat_notes_times = [note_timings[i] for i,t in zip(range(0, len(noteons)),on_beats)if noteons[i].velocity > 0 and t]
on_beat_notes_scale = np.asarray(on_beat_notes) % 2
off_beats = (note_timings+.5==(note_timings+.5).astype(int))
off_beat_notes = [n.note for n,t in zip(noteons,off_beats)if n.velocity > 0 and t]
off_beat_notes_times = [note_timings[i] for i,t in zip(range(0, len(noteons)),off_beats)if noteons[i].velocity > 0 and t]
off_beat_notes_scale = np.asarray(off_beat_notes) % 2

plt.figure(figsize=(7,1.3))
plt.scatter(on_beat_notes_times/note_timings[-1]*f.length, on_beat_notes_scale, c=[whole_tone_colours[1] if v else whole_tone_colours[0] for v in on_beat_notes_scale], s=2)
plt.gca().set_yticks([0, 1])
plt.gca().set_yticklabels(["C♮ whole-tone scale", "D♭ whole-tone scale"])
plt.xlabel("Time (seconds)")
plt.gca().set_ylim(-.5, 1.5)
plt.gca().set_xlim(0, 110.5)
plt.gca().yaxis.set_ticks_position('none')
plt.title("On-beat whole-tone scale (Entry of the Gladiators)")
sns.despine(left=True)
plt.tight_layout()
plt.savefig("whole-tone-melody-gladiators.png")
plt.show()

plt.figure(figsize=(7,1.3))
plt.scatter(off_beat_notes_times/note_timings[-1]*f.length, off_beat_notes_scale, c=[whole_tone_colours[1] if v else whole_tone_colours[0] for v in off_beat_notes_scale], s=2)
plt.gca().set_yticks([0, 1])
plt.gca().set_yticklabels(["C♮ whole-tone scale", "D♭ whole-tone scale"])
plt.xlabel("Time (seconds)")
plt.gca().set_ylim(-.5, 1.5)
plt.gca().set_xlim(0, 110.5)
plt.gca().yaxis.set_ticks_position('none')
plt.title("Off-beat whole-tone scale (Entry of the Gladiators)")
sns.despine(left=True)
plt.tight_layout()
plt.savefig("whole-tone-melody-gladiators-offbeats.png")
plt.show()
