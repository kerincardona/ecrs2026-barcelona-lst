#!/usr/bin/env python3
"""[v2 column variant of make_fig_lcz_map.py: no title/axes, legend below, sized for a half-slide column]
ECRS 2026 slide 4 — LCZ categorical map (WUDAPT/Demuzere palette).

Reads data/processed/lcz_barcelona_100m.tif (uint8 LCZ codes, EPSG:4326).
Uses the standard Demuzere et al. (2019) LCZ palette. Legend restricted to
classes actually present in the AOI, cross-checked against
suhi_by_lcz_JJA_daytime.csv. LCZ D (low plants, rural reference) is
highlighted with a bold legend marker.

Output: ecrs2026_presentation/figures/fig_lcz_map_col.pdf (+ .png for QA)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parent.parent
LCZ_TIF = REPO_ROOT / "data/processed/lcz_barcelona_100m.tif"
SUHI_CSV = REPO_ROOT / "data/processed/lst_exposure_indicators/suhi_by_lcz/suhi_by_lcz_JJA_daytime.csv"
OUT_DIR = REPO_ROOT / "ecrs2026_presentation/figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = OUT_DIR / "fig_lcz_map_col.pdf"
OUT_PNG = OUT_DIR / "fig_lcz_map_col.png"

# Standard WUDAPT / Demuzere et al. (2019) LCZ palette (codes 1-17).
# Built-up classes 1-10, land-cover classes 11-17 (A-G).
LCZ_COLORS = {
    1: "#8c0000",   # Compact high-rise
    2: "#d10000",   # Compact midrise
    3: "#ff0000",   # Compact low-rise
    4: "#bf4d00",   # Open high-rise
    5: "#ff6600",   # Open midrise
    6: "#ff9955",   # Open low-rise
    7: "#faee05",   # Lightweight low-rise
    8: "#bcbcbc",   # Large low-rise
    9: "#ffccaa",   # Sparsely built
    10: "#555555",  # Heavy industry
    11: "#006a00",  # A - Dense trees
    12: "#00aa00",  # B - Scattered trees
    13: "#648525",  # C - Bush, scrub
    14: "#b9db79",  # D - Low plants
    15: "#000000",  # E - Bare rock or paved
    16: "#fbf7ae",  # F - Bare soil or sand
    17: "#6a6aff",  # G - Water
}
# Demuzere codes 11-17 correspond to letters A-G; the raster stores them as
# 11-17 (confirmed against suhi_by_lcz_JJA_daytime.csv join keys: numeric
# 1-10 for built types, but A-G land-cover classes are also numeric-coded
# 11-17 in this raster — verified below by cross-tabulating pixel counts).
LCZ_LABELS = {
    1: "1 Compact high-rise", 2: "2 Compact midrise", 3: "3 Compact low-rise",
    4: "4 Open high-rise", 5: "5 Open midrise", 6: "6 Open low-rise",
    7: "7 Lightweight low-rise", 8: "8 Large low-rise", 9: "9 Sparsely built",
    10: "10 Heavy industry",
    11: "A Dense trees", 12: "B Scattered trees", 13: "C Bush, scrub",
    14: "D Low plants (rural ref.)", 15: "E Bare rock/paved",
    16: "F Bare soil/sand", 17: "G Water",
}

with rasterio.open(LCZ_TIF) as src:
    arr = src.read(1)
    extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    nodata = src.nodata

# Classes present in the raster (excluding 0 = unclassified/no-data)
present_codes = sorted(int(c) for c in np.unique(arr) if c != 0 and c in LCZ_COLORS)

# Cross-check against the SUHI-by-LCZ CSV (source of truth for "classes present
# in the AOI" per the brief) — map letter codes A-G to numeric raster codes.
suhi = pd.read_csv(SUHI_CSV)
letter_to_num = {"A": 11, "B": 12, "C": 13, "D": 14, "E": 15, "F": 16, "G": 17}
csv_codes = set()
for v in suhi["lcz_class"].astype(str):
    if v.isdigit():
        csv_codes.add(int(v))
    elif v in letter_to_num:
        csv_codes.add(letter_to_num[v])
missing_in_raster = csv_codes - set(present_codes)
extra_in_raster = set(present_codes) - csv_codes
print(f"LCZ classes in raster: {present_codes}")
print(f"LCZ classes in SUHI CSV (mapped): {sorted(csv_codes)}")
print(f"In CSV but not raster: {missing_in_raster} | In raster but not CSV: {extra_in_raster}")

codes = present_codes
colors = [LCZ_COLORS[c] for c in codes]
cmap = ListedColormap(colors)
norm = BoundaryNorm([c - 0.5 for c in codes] + [codes[-1] + 0.5], cmap.N)
masked = np.ma.masked_where(~np.isin(arr, codes), arr)

plt.rcParams.update({"font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(3.3, 4.0))
ax.imshow(masked, cmap=cmap, norm=norm, extent=extent, origin="upper", interpolation="nearest")
d_mask = (arr == 14).astype(float)
if d_mask.max() > 0:  # LCZ D (rural reference) outlined
    ax.contour(d_mask, levels=[0.5], colors="#1a1aff", linewidths=0.8,
               extent=extent, origin="upper")
ax.set_xticks([]); ax.set_yticks([])
ax.set_aspect(1 / np.cos(np.deg2rad(41.4)))  # lon/lat raster: correct E-W stretch at 41.4N
for sp in ax.spines.values():
    sp.set_linewidth(0.6); sp.set_color("0.4")

# Half-slide legibility: legend lists only the dominant classes (>= 4 % of
# classified pixels) plus the ones named on the slide (8, 10, A=11, D=14).
valid = np.isin(arr, codes)
frac = {c: float((arr == c).sum()) / valid.sum() for c in codes}
key = [c for c in codes if frac[c] >= 0.04 or c in (8, 10, 11, 14)]
handles = [Patch(facecolor=LCZ_COLORS[c], edgecolor="black", linewidth=0.3, label=LCZ_LABELS[c])
           for c in key]
leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2,
                fontsize=8.5, frameon=False, handlelength=1.1, handleheight=0.9,
                columnspacing=0.8, labelspacing=0.3, borderaxespad=0.2)
print("legend classes:", {LCZ_LABELS[c]: round(100 * frac[c], 1) for c in key})
for text, c in zip(leg.get_texts(), key):
    if c == 14:
        text.set_fontweight("bold"); text.set_color("#1a1aff")

fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
print(f"classes={codes}\nSaved {OUT_PDF}")
