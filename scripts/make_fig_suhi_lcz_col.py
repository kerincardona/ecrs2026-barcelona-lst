#!/usr/bin/env python3
"""ECRS 2026 deck v2, slide 5: SUHI by LCZ redrawn for a half-slide column.

The paper figure (fig1_suhi_by_lcz.png) has 15 classes and ~5 pt text once
shrunk into the column. This version is drawn at the exact column size
(2.70 x 2.65 in = \\linewidth x 0.80\\textheight of the v2 Beamer frame), so
fonts print at their nominal size (9-10 pt) on the slide:
  - only classes covering >= 2 % of the classified pixels (10 of 15; the
    omitted ones -- C, E, F, 1, 3 -- are listed in a footnote);
  - the three classes named on the slide (8, 10, A) in colour, the rest grey,
    LCZ D marked as the reference;
  - only the two extremes (LCZ 8, LCZ A) in colour, no value labels: the
    numbers are given once, large, in the slide text.
Data: data/processed/lst_exposure_indicators/suhi_by_lcz/suhi_by_lcz_JJA_daytime.csv
Output: ecrs2026_presentation/figures/fig_suhi_lcz_col.{pdf,png}
"""
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / "data/processed/lst_exposure_indicators/suhi_by_lcz/suhi_by_lcz_JJA_daytime.csv"
OUT = REPO / "ecrs2026_presentation/figures/fig_suhi_lcz_col"
WARM, COOL, GREY, NAVY = "#c0392b", "#2e7d32", "#b8b8b8", "#1b2a4a"
SHORT = {"8": "Large low-rise", "10": "Heavy industry", "2": "Compact midrise",
         "3": "Compact low-rise", "D": "Low plants", "4": "Open high-rise",
         "5": "Open midrise", "9": "Sparsely built", "6": "Open low-rise",
         "B": "Scattered trees", "A": "Dense trees"}

d = pd.read_csv(CSV, dtype={"lcz_class": str})
d["share"] = d.pixel_count / d.pixel_count.sum()
keep = d[d.share >= 0.02].sort_values("suhi_intensity_K").reset_index(drop=True)
drop = d[d.share < 0.02].lcz_class.tolist()
gap = float(d.loc[d.lcz_class == "8", "median_lst_K"].iloc[0] - d.loc[d.lcz_class == "A", "median_lst_K"].iloc[0])

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(2.70, 2.65))
fig.subplots_adjust(left=0.475, right=0.985, top=0.985, bottom=0.185)
y = range(len(keep))
col = [WARM if c == "8" else COOL if c == "A" else GREY for c in keep.lcz_class]
ax.barh(list(y), keep.suhi_intensity_K, color=col, height=0.72, zorder=2)
ax.axvline(0, color="0.25", lw=0.8, zorder=3)
labels = []
for c in keep.lcz_class:
    lab = f"{c}  {SHORT[c]}"
    labels.append(lab + " (ref.)" if c == "D" else lab)
ax.set_yticks(list(y), labels, fontsize=8)
for t, c in zip(ax.get_yticklabels(), keep.lcz_class):
    if c == "8":
        t.set_color(WARM); t.set_fontweight("bold")
    elif c == "A":
        t.set_color(COOL); t.set_fontweight("bold")
ax.tick_params(axis="y", length=0, pad=3)
# No value labels: the two extremes are stated (large) in the slide text;
# the chart only carries the ranking and the asymmetry.
# The LCZ 8 - LCZ A gap is stated in the slide text, not repeated here
# (one number, one place).
ax.set_xlim(-9.2, 2.4)
ax.set_xticks([-8, -4, 0])
ax.tick_params(axis="x", labelsize=8.5, length=2)
ax.set_xlabel("SUHI vs LCZ D (K)", fontsize=8.5, labelpad=2)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="0.92", lw=0.6, zorder=0)
fig.text(0.02, 0.012, f"Classes < 2 % of area omitted ({', '.join(drop)}).", fontsize=6.5,
         color="0.4", ha="left", va="bottom")
for e in ("pdf", "png"):
    fig.savefig(f"{OUT}.{e}", dpi=300)
print(keep[["lcz_class", "suhi_intensity_K", "share"]].round(3).to_string(index=False))
print(f"omitted (<2 %): {drop}; LCZ 8 - LCZ A = {gap:.2f} K")
