#!/usr/bin/env python3
"""Hotspot-frequency map, v2 (slide 6 column figure + paper Fig. 2 replacement).

Fixes two defects of the v1 map (fig_hotspot_crop_slide6.png / fig2_lst_hotspot_map):
  1. pixels with zero exceedances (Collserola, sea) were drawn white, the same
     colour as the TOP of the colour scale -> the coolest area read as hottest;
  2. axes in UTM metres with a "1e6" offset, x-axis labelled "Longitude".

v2:
  - sea / water masked from the LCZ map (class 0 = offshore no-data, 17 = G)
    and drawn flat light blue;
  - land with f_hs = 0 ("never above P90") in neutral grey, outside the scale;
  - f_hs > 0 in discrete YlOrRd classes with edges 0, 0.1, 0.2, 0.29, 0.5, 0.7
    (0.29 = top-decile cut used in the paper, 0.5 = slide's "persistent");
  - no axes; scale bar (exact, UTM) + north arrow; a few labels
    (OSM Nominatim, queried 2026-10-08).
Paper version adds panel (a): JJA median LST (deg C), same masking.

Data: hotspot_frequency_JJA_30m.tif (compute_hotspots.py; f = N_exceed/153),
      lst_median_JJA_daytime.tif, lcz_barcelona_100m.tif.
Outputs (new files, v1 untouched):
  ecrs2026_presentation/figures/fig_hotspot_col.{pdf,png}
  paper/figures/fig2_lst_hotspot_map_v2.{pdf,png}
Run: .venv/bin/python scripts/make_fig_hotspot_v2.py
"""
from pathlib import Path

import numpy as np
import rioxarray  # noqa: F401
from rasterio.enums import Resampling
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle

REPO = Path(__file__).resolve().parent.parent
HS = REPO / "data/processed/lst_exposure_indicators/hotspot_frequency_JJA_30m.tif"
LST = REPO / "data/processed/lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif"
LCZ = REPO / "data/processed/lcz_barcelona_100m.tif"
OUT_SLIDE = REPO / "ecrs2026_presentation/figures/fig_hotspot_col"
OUT_PAPER = REPO / "paper/figures/fig2_lst_hotspot_map_v2"

SEA = "#d6e4ef"
ZERO = "#bdbdbd"
EDGES = [0.0, 0.1, 0.2, 0.29, 0.5, 0.7]
PLACES = {  # (lat, lon), OSM Nominatim 2026-10-08
    "Zona Franca": (41.3430, 2.1450),
    "Port": (41.3388, 2.1593),
    "Collserola": (41.4232, 2.1199),   # Tibidabo summit
    "Barcelona": (41.3826, 2.1771),
}

hs = rioxarray.open_rasterio(HS, masked=True).squeeze(drop=True)
lst = rioxarray.open_rasterio(LST, masked=True).squeeze(drop=True)
assert hs.shape == lst.shape and hs.rio.transform() == lst.rio.transform()
lcz = rioxarray.open_rasterio(LCZ, masked=True).squeeze(drop=True).rio.reproject_match(
    lst, resampling=Resampling.nearest).values
L, B, R, T = lst.rio.bounds()
ext = (L, R, B, T)
F, M = hs.values.astype(float), lst.values.astype(float)
land = (lcz >= 1) & (lcz <= 16) & np.isfinite(M)
sea = ~land
thr = float(hs.attrs.get("threshold_K", np.nan))
print(f"land px {land.sum()}, f=0 on land {100 * np.mean(F[land] == 0):.1f} %, "
      f">=1 event {100 * np.mean(F[land] > 0):.1f} %, f>0.5 {100 * np.mean(F[land] > 0.5):.2f} %")

cmap_hs = ListedColormap(plt.get_cmap("YlOrRd")(np.linspace(0.15, 1.0, len(EDGES) - 1)))
norm_hs = BoundaryNorm(EDGES, cmap_hs.N)
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)
halo = [pe.withStroke(linewidth=2.0, foreground="white")]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})


def base(ax):
    ax.imshow(np.where(sea, 1.0, np.nan), extent=ext, cmap=ListedColormap([SEA]),
              interpolation="nearest", zorder=0)
    ax.set_xlim(L, R); ax.set_ylim(B, T); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_linewidth(0.6); sp.set_color("0.4")


def furniture(ax, labels=True, fs=8):
    if labels:
        for name, (lat, lon) in PLACES.items():
            x, y = to_utm.transform(lon, lat)
            kw = dict(fontsize=fs, color="0.1", ha="center", va="center", zorder=6, path_effects=halo)
            if name == "Port":
                kw.update(ha="left"); x += 600; y -= 350
            if name == "Zona Franca":
                kw.update(ha="right"); x -= 300; y -= 250
            if name == "Collserola":
                kw.update(fontstyle="italic", color="#2e6b30")
            if name == "Barcelona":
                kw.update(fontweight="bold", color="#1b2a4a"); y += 900
            ax.plot(x, y, alpha=0)
            ax.text(x, y, name, **kw)
        sx, sy = to_utm.transform(2.212, 41.318)
        ax.text(sx, sy, "Mediterranean\nSea", fontsize=fs - 0.5, fontstyle="italic",
                color="#3d6f99", ha="center", va="center", zorder=6, linespacing=1.0)
    sb_x, sb_y, sb_len = L + 900, B + 900, 5000
    ax.add_patch(Rectangle((sb_x, sb_y), sb_len / 2, 220, facecolor="black", zorder=7))
    ax.add_patch(Rectangle((sb_x + sb_len / 2, sb_y), sb_len / 2, 220, facecolor="white",
                           edgecolor="black", linewidth=0.5, zorder=7))
    ax.text(sb_x + sb_len / 2, sb_y + 380, "5 km", ha="center", va="bottom", fontsize=fs - 1.5,
            zorder=7, path_effects=halo)
    nx, ny = R - 1100, T - 3000
    ax.annotate("", xy=(nx, ny + 1700), xytext=(nx, ny), zorder=7,
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.0, mutation_scale=8))
    ax.text(nx, ny + 1850, "N", ha="center", va="bottom", fontsize=fs - 0.5, fontweight="bold",
            zorder=7, path_effects=halo)


def hotspot_panel(ax, cax, fs=8, cbar_orient="horizontal"):
    base(ax)
    ax.imshow(np.where(land & (F == 0), 1.0, np.nan), extent=ext,
              cmap=ListedColormap([ZERO]), interpolation="nearest", zorder=1)
    im = ax.imshow(np.where(land & (F > 0), F, np.nan), extent=ext, cmap=cmap_hs, norm=norm_hs,
                   interpolation="nearest", zorder=2)
    furniture(ax, fs=fs)
    cb = plt.colorbar(im, cax=cax, orientation=cbar_orient, spacing="proportional",
                      ticks=EDGES)
    cb.ax.tick_params(labelsize=fs - 1, length=2)
    lab = f"Share of summer scenes above P$_{{90}}$ ({thr:.1f} K)"
    (cb.set_label(lab, fontsize=fs - 0.5) if cbar_orient == "horizontal"
     else cb.set_label(lab, fontsize=fs - 0.5))
    return cb


# ---------------------------------------------------------------- slide (column)
# Map + vertical colour bar on the right: overall aspect ~1.15, which matches
# the half-slide column box (0.49 textwidth x 0.80 textheight), so the map is
# width-limited rather than height-limited and labels stay legible.
H_IN = 3.6
w_map = H_IN * (R - L) / (T - B)
W_IN = w_map + 1.05
fig = plt.figure(figsize=(W_IN, H_IN))
ax = fig.add_axes([0, 0, w_map / W_IN, 1])
cax = fig.add_axes([(w_map + 0.12) / W_IN, 0.36, 0.11 / W_IN, 0.60])
cb = hotspot_panel(ax, cax, fs=8.5, cbar_orient="vertical")
cb.set_label(f"Share of summer scenes\nabove P$_{{90}}$ = {thr:.1f} K", fontsize=7.5)
fig.legend(handles=[Patch(facecolor=ZERO, edgecolor="0.4", linewidth=0.4, label="never"),
                    Patch(facecolor=SEA, edgecolor="0.4", linewidth=0.4, label="sea")],
           loc="lower left", bbox_to_anchor=((w_map + 0.04) / W_IN, 0.04), frameon=False,
           fontsize=7.5, handlelength=1.1, handleheight=0.9, labelspacing=0.3)
for ext_ in ("pdf", "png"):
    fig.savefig(f"{OUT_SLIDE}.{ext_}", dpi=300)
plt.close(fig)

# ---------------------------------------------------------------- paper (2 panels)
fig, (a0, a1) = plt.subplots(1, 2, figsize=(10, 5.6))
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.17, wspace=0.06)
base(a0)
Mc = M - 273.15
vmin, vmax = np.nanpercentile(Mc[land], [2, 98])
im0 = a0.imshow(np.where(land, Mc, np.nan), extent=ext, cmap="RdYlBu_r", vmin=vmin, vmax=vmax,
                interpolation="nearest", zorder=1)
furniture(a0, fs=8.5)
a0.set_title("(a) JJA daytime median LST, 2013–2024", loc="left", fontsize=10)
c0 = fig.add_axes([0.06, 0.10, 0.40, 0.022])
cb0 = plt.colorbar(im0, cax=c0, orientation="horizontal", extend="both")
cb0.set_label("LST (°C), 2–98 % range over land", fontsize=8.5)
cb0.ax.tick_params(labelsize=8)
c1 = fig.add_axes([0.54, 0.10, 0.30, 0.022])
hotspot_panel(a1, c1, fs=8.5)
a1.set_title("(b) Hotspot frequency $f_{\\mathrm{hs}}$ (JJA)", loc="left", fontsize=10)
fig.legend(handles=[Patch(facecolor=ZERO, edgecolor="0.4", linewidth=0.4, label="never above P$_{90}$"),
                    Patch(facecolor=SEA, edgecolor="0.4", linewidth=0.4, label="sea / water")],
           loc="lower left", bbox_to_anchor=(0.855, 0.065), frameon=False, fontsize=8,
           handlelength=1.1, handleheight=0.9, labelspacing=0.3)
for ext_ in ("pdf", "png"):
    fig.savefig(f"{OUT_PAPER}.{ext_}", dpi=300)
print(f"P90 = {thr:.2f} K; LST colour range {vmin:.1f}-{vmax:.1f} C")
print("saved", OUT_SLIDE, OUT_PAPER)
