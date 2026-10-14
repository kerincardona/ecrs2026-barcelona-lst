#!/usr/bin/env python3
"""ECRS 2026 deck v2, slide 7: validation panel, stacked for a half-slide column.

Same data and encoding as make_fig_validation_panel.py (v1, side-by-side), but
two rows instead of two columns so it fits the right column of the v2
two-column layout. All numbers are read from the validation JSONs.

Output: ecrs2026_presentation/figures/fig_validation_panel_col.{pdf,png}
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
ERA5_JSON = REPO / "data/processed/validation/validation_era5.json"
ECO_JSON = REPO / "data/processed/validation/validation_ecostress.json"
OUT_DIR = REPO / "ecrs2026_presentation/figures"
OUT_PDF = OUT_DIR / "fig_validation_panel_col.pdf"
OUT_PNG = OUT_DIR / "fig_validation_panel_col.png"

WARM, COOL = "#c0392b", "#2c6fbb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})

era5 = json.loads(ERA5_JSON.read_text())
eco = json.loads(ECO_JSON.read_text())

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(3.7, 4.3), gridspec_kw={"hspace": 0.62})

# (a) ERA5-Land seasonal bias
order = ["DJF", "MAM", "JJA", "SON"]
bs = era5["by_season"]
seas = [s for s in order if s in bs]
bias = [bs[s]["bias_K"] for s in seas]
rv = [bs[s]["pearson_r"] for s in seas]
x = np.arange(len(seas))
ax.bar(x, bias, color=[WARM if b >= 0 else COOL for b in bias], edgecolor="black",
       linewidth=0.4, width=0.55)
ax.axhline(0, color="black", linewidth=0.7)
ax.set_xticks(x, seas)
ax.set_ylabel("ERA5 − Landsat (K)")
ax.set_title(f"(a) ERA5-Land  ·  pooled r = {era5['pearson_r']:.2f}, n = {era5['n_pairs']}",
             fontsize=8.5, loc="left")
for xi, b, r in zip(x, bias, rv):
    ax.text(xi, b - 0.25, f"r={r:.2f}", ha="center", va="top", fontsize=7)
ax.set_ylim(min(bias) - 1.6, 0.5)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines[["top", "right"]].set_visible(False)

# (b) ECOSTRESS per-scene bias
sc = eco["by_scene"]
sb = [s["bias_K"] for s in sc]
x2 = np.arange(len(sc))
ax2.bar(x2, sb, color=[WARM if b >= 0 else COOL for b in sb], edgecolor="black",
        linewidth=0.4, width=0.6)
ax2.axhline(0, color="black", linewidth=0.7)
ax2.set_xticks(x2, [s["date"][2:] for s in sc], rotation=40, ha="right", fontsize=6.5)
ax2.set_ylabel("ECOSTRESS − Landsat (K)")
ax2.set_title(f"(b) ECOSTRESS 70 m  ·  {eco['n_scenes']} scenes", fontsize=8.5, loc="left")
ax2.text(0.02, 0.97,
         f"bias {eco['bias_K']:+.2f} K · RMSE {eco['rmse_K']:.1f} K · r = {eco['pearson_r']:.2f}",
         transform=ax2.transAxes, fontsize=7, va="top", ha="left",
         bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="0.6"))
lo, hi = min(sb), max(sb)
ax2.set_ylim(lo - 1.0, hi + 3.2)
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.spines[["top", "right"]].set_visible(False)

fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
print(f"ERA5 pooled r={era5['pearson_r']:.4f} n={era5['n_pairs']} | by season r:",
      {s: round(bs[s]['pearson_r'], 3) for s in seas})
print(f"ECOSTRESS bias={eco['bias_K']:.4f} rmse={eco['rmse_K']:.4f} r={eco['pearson_r']:.4f}")
print(f"Saved {OUT_PDF}")
