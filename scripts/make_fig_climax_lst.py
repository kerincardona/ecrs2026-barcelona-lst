#!/usr/bin/env python3
"""ECRS 2026 slide 8 — climax slide: single full-screen LST median JJA map.

Single panel, median JJA daytime LST only, from
lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif. No text except
colorbar (K) and scale bar, per the "climax slide" rule (one figure, no
bullets, >=80% of the slide).

Output: ecrs2026_presentation/figures/fig_climax_lst_jja.pdf (+ .png for QA)
"""
from pathlib import Path

import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
LST_TIF = REPO_ROOT / "data/processed/lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif"
OUT_DIR = REPO_ROOT / "ecrs2026_presentation/figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = OUT_DIR / "fig_climax_lst_jja.pdf"
OUT_PNG = OUT_DIR / "fig_climax_lst_jja.png"

with rasterio.open(LST_TIF) as src:
    arr = src.read(1)
    extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    res_x, res_y = src.res

arr_c = arr - 273.15  # K -> degC for readability (still read from the raster, not hardcoded)
masked = np.ma.masked_invalid(arr_c)

vmin, vmax = np.nanpercentile(arr_c.compressed() if hasattr(arr_c, "compressed") else arr_c, [1, 99])

fig, ax = plt.subplots(figsize=(14.2, 9.2))  # wide, screen-filling aspect for a slide
im = ax.imshow(masked, cmap="inferno", vmin=vmin, vmax=vmax, extent=extent, origin="upper")
ax.set_axis_off()

cbar = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
cbar.set_label("LST, median JJA daytime (°C)", fontsize=12)
cbar.ax.tick_params(labelsize=10)

# Scale bar (5 km, computed from raster resolution in projected CRS units - meters)
bar_m = 5000.0
x0 = extent[0] + (extent[1] - extent[0]) * 0.04
y0 = extent[2] + (extent[3] - extent[2]) * 0.05
ax.plot([x0, x0 + bar_m], [y0, y0], color="white", linewidth=4, solid_capstyle="butt",
        path_effects=None, zorder=5)
ax.plot([x0, x0 + bar_m], [y0, y0], color="black", linewidth=1.2, solid_capstyle="butt", zorder=6)
ax.text(x0 + bar_m / 2, y0 + (extent[3] - extent[2]) * 0.018, "5 km",
        ha="center", va="bottom", fontsize=11, color="white",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="black", alpha=0.55, edgecolor="none"))

fig.subplots_adjust(left=0.01, right=0.97, top=0.99, bottom=0.01)
fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.05)
fig.savefig(OUT_PNG, dpi=220, bbox_inches="tight", pad_inches=0.05)
print(f"LST range (1-99 pct) degC: [{vmin:.2f}, {vmax:.2f}]")
print(f"raster resolution: {res_x:.1f} x {res_y:.1f} m")
print(f"Saved {OUT_PDF}")
print(f"Saved {OUT_PNG}")
