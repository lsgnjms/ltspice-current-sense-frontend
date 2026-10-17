#!/usr/bin/env python3
"""Plot the ngspice reference results and compute the headline metrics.

Reads results/data/{tran,dc,ac}.txt (written by scripts/run_ngspice.sh) and
writes results/plots/*.png plus results/summary.txt.

Usage:  python3 scripts/plot_reference.py      (needs numpy, matplotlib)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "results" / "data"
PLOTS = ROOT / "results" / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2, "legend.frameon": False,
})


def load(name):
    with open(DATA / name) as f:
        header = f.readline().split()
    return header, np.loadtxt(DATA / name, skiprows=1)


# ---- Transient -------------------------------------------------------------
_, tr = load("tran.txt")
t, vs, vo = tr[:, 0] * 1e3, tr[:, 1], tr[:, 2]   # time in ms

# Plateau = samples well inside the "on" phase of each pulse (2-4.5 ms after edge)
phase = (tr[:, 0] - 1e-3) % 10e-3
on = (tr[:, 0] > 1e-3) & (phase > 1e-3) & (phase < 3.5e-3)
plateau_sense = vs[on].mean()
plateau_vout = vo[on].mean()

fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
a1.plot(t, vs * 1e3, color=BLUE)
a1.set_ylabel("V(sense) [mV]")
a1.set_title("Transient: 0-2 A pulsed load (4 ms on, 10 ms period)", loc="left")
a1.annotate(f"{plateau_sense*1e3:.1f} mV", xy=(3, plateau_sense * 1e3),
            xytext=(0, 6), textcoords="offset points", ha="center", color=INK)
a2.plot(t, vo, color=ORANGE)
a2.set_ylabel("V(vout) [V]")
a2.set_xlabel("Time [ms]")
a2.annotate(f"{plateau_vout:.4f} V", xy=(3, plateau_vout),
            xytext=(0, 6), textcoords="offset points", ha="center", color=INK)
for ax in (a1, a2):
    ax.set_ylim(bottom=-0.05 * ax.get_ylim()[1], top=ax.get_ylim()[1] * 1.15)
fig.savefig(PLOTS / "transient.png")
plt.close(fig)

# ---- DC sweep --------------------------------------------------------------
_, dc = load("dc.txt")
i, dvs, dvo = dc[:, 0], dc[:, 1], dc[:, 2]
gain, offset = np.polyfit(i, dvo, 1)
ideal = 1.0 * i                       # 1 V/A target
err_mv = (dvo - ideal) * 1e3
max_err_mv = np.max(np.abs(err_mv))

fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
a1.plot(i, dvo, color=ORANGE, label="V(vout) simulated")
a1.plot(i, ideal, color=MUTED, linewidth=1, linestyle="--", label="Ideal 1 V/A")
a1.set_ylabel("V(vout) [V]")
a1.set_title(f"DC sweep: transfer gain {gain:.4f} V/A", loc="left")
a1.legend(loc="upper left")
a2.plot(i, err_mv, color=BLUE)
a2.set_ylabel("Error vs ideal [mV]")
a2.set_xlabel("Load current [A]")
fig.savefig(PLOTS / "dc_sweep.png")
plt.close(fig)

# ---- AC sweep --------------------------------------------------------------
_, ac = load("ac.txt")
f, mag, ph = ac[:, 0], ac[:, 1], ac[:, 2]
dc_db = mag[0]
idx = np.argmax(mag < dc_db - 3)
# log-interpolate the -3 dB crossing
f3 = 10 ** np.interp(dc_db - 3, [mag[idx], mag[idx - 1]],
                     [np.log10(f[idx]), np.log10(f[idx - 1])])

fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
a1.semilogx(f, mag, color=BLUE)
a1.axvline(f3, color=MUTED, linewidth=1, linestyle="--")
a1.annotate(f"-3 dB at {f3/1e3:.1f} kHz", xy=(f3, dc_db - 3),
            xytext=(8, 0), textcoords="offset points", color=INK, va="center")
a1.set_ylabel("|V(vout)/I(load)| [dB V/A]")
a1.set_title("AC sweep: closed-loop response (bias 1 A)", loc="left")
a2.semilogx(f, ph, color=ORANGE)
a2.axvline(f3, color=MUTED, linewidth=1, linestyle="--")
a2.set_ylabel("Phase [deg]")
a2.set_xlabel("Frequency [Hz]")
fig.savefig(PLOTS / "ac_response.png")
plt.close(fig)

# ---- Summary ---------------------------------------------------------------
summary = f"""Current-sense front-end: ngspice reference results
Peak V(sense) at 2 A          {plateau_sense*1e3:.2f} mV
V(vout) plateau at 2 A        {plateau_vout:.4f} V
DC transfer gain (fit)        {gain:.5f} V/A   (offset {offset*1e6:.2f} uV)
Max DC error, 0-2 A sweep     {max_err_mv:.3f} mV
Low-frequency gain            {dc_db:.4f} dB V/A
Closed-loop -3 dB bandwidth   {f3/1e3:.1f} kHz
"""
(ROOT / "results" / "summary.txt").write_text(summary)
print(summary)
