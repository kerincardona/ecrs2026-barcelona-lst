#!/usr/bin/env python3
"""ECRS 2026 deck v2, slide 9: census-tract exposure, maximised for the column.

Same data and encoding as make_fig_censustract_col.py (median JJA LST in a
30 m building buffer per census section, Barcelona city, inferno, P2-P98),
but laid out to use the full height of the slide column:
  - no external colour bar (the horizontal bar of the _col version ate ~25 %
    of the height, and the map is portrait, so height is the limit);
  - figure drawn at its printed size (map height ~2.9 in), so fonts are nominal;
  - district boundaries (dissolved from DISTRICTE) as thin white lines and
    three orientation labels (OSM Nominatim, 2026-10-08).
  - colour bar inset in the empty SW corner, so the figure is the map only.\nOutput: ecrs2026_presentation/figures/fig_censustract_tall.{pdf,png}
(fig_censustract_col.* and the paper figure are untouched.)
"""
from pathlib import Path

import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from pyproj import Transformer

REPO = Path(__file__).resolve().parent.parent
GPKG = REPO / "data/processed/lst_exposure_indicators/censustract_lst_exposure.gpkg"
OUT = REPO / "ecrs2026_presentation/figures/fig_censustract_tall"
PLACES = {"Eixample": (41.3920, 2.1640), "Zona Franca": (41.3430, 2.1450),
          "Collserola": (41.4232, 2.1199)}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
g = gpd.read_file(GPKG)
g["median_C"] = g["lst_median_30m"] - 273.15
vmin, vmax = np.nanpercentile(g["median_C"], [2, 98])
dist = g.dissolve(by="DISTRICTE")
L, B, R, T = g.total_bounds
pad = 250
L, B, R, T = L - pad, B - pad, R + pad, T + pad

H_IN = 3.2
W_IN = H_IN * (R - L) / (T - B)   # map only: colour bar sits inside the empty SW corner
fig = plt.figure(figsize=(W_IN, H_IN))
ax = fig.add_axes([0, 0, 1, 1])
g.plot(column="median_C", ax=ax, cmap="inferno", vmin=vmin, vmax=vmax,
       edgecolor="0.55", linewidth=0.06)
dist.boundary.plot(ax=ax, color="white", linewidth=0.7, alpha=0.9)
ax.set_xlim(L, R); ax.set_ylim(B, T); ax.set_aspect("equal"); ax.set_axis_off()

to_xy = Transformer.from_crs("EPSG:4326", g.crs, always_xy=True)
halo = [pe.withStroke(linewidth=2.2, foreground="white")]
for name, (lat, lon) in PLACES.items():
    x, y = to_xy.transform(lon, lat)
    kw = dict(fontsize=8.5, ha="center", va="center", color="0.1", path_effects=halo, zorder=5)
    if name == "Collserola":
        kw.update(fontstyle="italic", color="#2e6b30")
    if name == "Zona Franca":
        y -= 900  # centre of the yellow logistics area, below the point
    ax.text(x, y, name, **kw)

# 2 km scale bar + north arrow (projected CRS, metres)
sx, sy = L + 9000, B + 600
ax.plot([sx, sx + 2000], [sy, sy], color="black", lw=2.2, solid_capstyle="butt")
ax.text(sx + 1000, sy + 250, "2 km", ha="center", va="bottom", fontsize=7.5, path_effects=halo)
nx, ny = R - 900, T - 2300
ax.annotate("", xy=(nx, ny + 1300), xytext=(nx, ny),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0, mutation_scale=8))
ax.text(nx, ny + 1450, "N", ha="center", va="bottom", fontsize=8, fontweight="bold")

cax = ax.inset_axes([0.035, 0.07, 0.035, 0.36])   # SW corner, outside the city limits
sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(vmin=vmin, vmax=vmax))
cb = fig.colorbar(sm, cax=cax, extend="both", ticks=np.arange(np.ceil(vmin), vmax + 0.01, 1.0))
cb.ax.tick_params(labelsize=8, length=2)
cax.set_title("LST\n(°C)", fontsize=8, loc="left", pad=4)
for e in ("pdf", "png"):
    fig.savefig(f"{OUT}.{e}", dpi=300)
print(f"n={len(g)}  range P2-P98 {vmin:.1f}-{vmax:.1f} C  size {W_IN:.2f}x{H_IN:.2f} in")
