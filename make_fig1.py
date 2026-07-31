#!/usr/bin/env python3
"""Figure 1 for the EduHPC-2026 short paper. Single IEEE column, portrait.

All values are measured on the reference machine (Apple M1, 4 P-cores +
4 E-cores, 8 GB, macOS 26.5, cc -O2). See reference_results.csv.

Identity is never carried by hue alone: every curve has its own marker, its
own dash pattern, and a direct end label, so the figure survives grayscale
printing and photocopying.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# Validated categorical slots 1-5 (light surface).
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d8d8d5"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5, "axes.titlesize": 7.5,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "text.color": INK, "axes.labelcolor": INK,
})

# ---- measured data -------------------------------------------------------
# (label, colour, marker, dashes, x, speedup)
CURVES = [
    ("cyclic schedule",   ORANGE, "s", (4, 1.6),      [1, 2, 4, 8],          [1.00, 1.93, 3.68, 5.82]),
    ("independent work",  BLUE,   "o", (),            [1, 2, 3, 4, 5, 6, 7, 8],
                                                      [1.00, 1.93, 2.79, 3.73, 4.21, 4.32, 5.15, 5.45]),
    ("block schedule",    AQUA,   "^", (1.2, 1.2),    [1, 2, 4, 8],          [1.00, 1.33, 2.15, 3.75]),
    ("task graph",        YELLOW, "D", (5, 1.5, 1, 1.5), [1, 2, 3, 4, 6, 8], [0.98, 1.47, 1.84, 1.85, 1.84, 1.85]),
    ("shared counter",    VIOLET, "X", (2.5, 1.2, 0.8, 1.2), [1, 2, 4, 8],   [1.00, 0.61, 0.29, 0.30]),
]

# Panel (b): one bar per lab, at 8 threads.
BARS = [
    ("Lab 2  cyclic\nnothing is waiting",        5.82, ORANGE, ""),
    ("Lab 2  block\nwaiting on an unequal split", 3.75, AQUA,  ""),
    ("Lab 1  task graph\nwaiting on the arrows",  1.85, YELLOW, ""),
    ("Lab 3  shared counter\nwaiting on each other", 0.30, VIOLET, "///"),
]
CEILING = 5.45   # Lab 4: what this machine actually delivers on 8 threads

fig, (ax, bx) = plt.subplots(
    2, 1, figsize=(3.38, 4.35), dpi=400,
    gridspec_kw={"height_ratios": [1.18, 1.0], "hspace": 0.50})

# ---- (a) speedup vs threads ---------------------------------------------
ax.plot([1, 8], [1, 8], color=MUTED, lw=0.7, dashes=(3, 2), zorder=1)
ax.text(4.5, 4.72, "perfect speedup", rotation=38, fontsize=5.8,
        color=MUTED, ha="center", va="bottom", rotation_mode="anchor")

for label, c, mk, dash, xs, ys in CURVES:
    ax.plot(xs, ys, color=c, lw=1.4, dashes=dash, marker=mk, ms=3.4,
            mew=0, zorder=3, solid_capstyle="round")

# Direct labels, so identity never depends on colour.
for label, c, xoff, yoff, ha in [
        ("cyclic",      ORANGE, 8.18, 5.95, "left"),
        ("independent", BLUE,   8.18, 5.05, "left"),
        ("block",       AQUA,   8.18, 3.75, "left"),
        ("task graph",  YELLOW, 8.18, 1.95, "left"),
        ("counter",     VIOLET, 8.18, 0.34, "left")]:
    ax.text(xoff, yoff, label, color=c, fontsize=6.2, ha=ha, va="center",
            fontweight="bold")

ax.set_xlim(0.6, 11.6); ax.set_ylim(0, 8.6)
ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8])
ax.yaxis.set_major_locator(MultipleLocator(2))
ax.set_xlabel("threads")
ax.set_ylabel("speedup over one thread")
ax.set_title("(a)  Every gap is somebody waiting",
             loc="left", pad=6, fontweight="bold")
ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
ax.axhline(1.0, color=MUTED, lw=0.5, dashes=(1, 2), zorder=2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

# ---- (b) the eight-thread ladder ----------------------------------------
ys = range(len(BARS))
for y, (label, v, c, hatch) in zip(ys, BARS):
    bx.barh(y, v, height=0.62, color=c, hatch=hatch, edgecolor="white",
            linewidth=0.8, zorder=3)
    bx.text(v + 0.12, y, f"{v:.2f}×", va="center", ha="left",
            fontsize=6.6, color=INK, fontweight="bold", zorder=4)

bx.axvline(CEILING, color=MUTED, lw=0.8, dashes=(3, 2), zorder=2)
bx.text(CEILING + 0.14, -0.78,
        f"Lab 4: what these 8 threads\nactually deliver ({CEILING:.2f}×)",
        fontsize=5.6, color=MUTED, ha="left", va="center", linespacing=1.3)
bx.axvline(1.0, color=MUTED, lw=0.5, dashes=(1, 2), zorder=2)
bx.text(1.12, len(BARS) - 0.45, "one thread", fontsize=5.6, color=MUTED,
        ha="left", va="center")

bx.set_yticks(list(ys))
bx.set_yticklabels([b[0] for b in BARS], fontsize=6.0, linespacing=1.35)
bx.set_ylim(len(BARS) - 0.1, -1.15)     # inverted, with headroom for the note
bx.set_xlim(0, 7.6); bx.set_xlabel("speedup on the same 8 threads")
bx.xaxis.set_major_locator(MultipleLocator(2))
bx.set_title("(b)  Same machine, same 8 threads, four ceilings",
             loc="left", pad=5, fontweight="bold")
bx.grid(axis="x", color=GRID, lw=0.5, zorder=0)
for s in ("top", "right", "left"):
    bx.spines[s].set_visible(False)
bx.tick_params(axis="y", length=0)

fig.savefig("fig1_four_ways_to_wait.png", bbox_inches="tight", pad_inches=0.02,
            facecolor="white")
print("wrote fig1_four_ways_to_wait.png")
