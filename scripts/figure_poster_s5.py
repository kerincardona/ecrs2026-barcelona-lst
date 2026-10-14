#!/usr/bin/env python3
"""Print-size figures for the ECRS 2026 poster of Abstract 1 (Session S5, SUHI by LCZ).

Poster mode (same rule as figure_poster_example.py --print-width-cm): figsize equals the
physical size on the A0 sheet, so every font size in pt is the printed size (>= 24 pt,
venue spec). PNG at 300 dpi + vector PDF.

Outputs (conference/ECRS2026/):
  fig_s5_maps.{png,pdf}        (a) JJA median LST  (b) hotspot frequency
                               (c) building-buffer LST by census section (Barcelona city)
  fig_s5_suhi.{png,pdf}        SUHI by LCZ, 8 main classes (poster middle column, 25 cm)
  fig_s5_provenance.json       every number the poster quotes, read from the source files

Sources (all local, no hard-coded results):
  data/processed/lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif
  data/processed/lst_exposure_indicators/hotspot_frequency_JJA_30m.tif (+ hotspot_land_sensitivity.json)
  data/processed/lcz_barcelona_100m.tif
  data/processed/lst_exposure_indicators/suhi_by_lcz/{suhi_by_lcz_JJA_daytime.csv, lcz_elevation_confound.json}
  data/processed/rq3_drivers/rq3_ml_elevfix_results_land.json  (summary.copdem = paper numbers)
  data/processed/validation/{validation_era5.json, validation_ecostress.json}
  data/processed/lst_exposure_indicators/building_exposure/building_lst_exposure.parquet
  data/processed/lst_exposure_indicators/censustract_lst_exposure_clean.parquet

Map styling replicates scripts/make_fig_hotspot_v2.py (paper Fig. 2 v2).
Run: .venv/bin/python scripts/figure_poster_s5.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
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
P = REPO / "data/processed"
HS = P / "lst_exposure_indicators/hotspot_frequency_JJA_30m.tif"
LST = P / "lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif"
LCZ = P / "lcz_barcelona_100m.tif"
SUHI = P / "lst_exposure_indicators/suhi_by_lcz/suhi_by_lcz_JJA_daytime.csv"
CENSUS = P / "lst_exposure_indicators/censustract_lst_exposure_clean.gpkg"
OUT = REPO / "conference/ECRS2026"

CM = 1 / 2.54
FS = 24          # minimum printed size, pt
SEA, ZERO = "#d6e4ef", "#bdbdbd"
WARM, COOL = "#c0392b", "#2c6fbb"
EDGES = [0.0, 0.1, 0.2, 0.29, 0.5, 0.7]
PLACES = {  # (lat, lon), OSM Nominatim 2026-10-08 (as make_fig_hotspot_v2.py)
    "Zona Franca": (41.3430, 2.1450),
    "Port": (41.3388, 2.1593),
    "Collserola": (41.4232, 2.1199),
    "Barcelona": (41.3826, 2.1771),
}
plt.rcParams.update({"font.family": "Arial", "font.size": FS,
                     "axes.linewidth": 1.2, "xtick.major.width": 1.2, "ytick.major.width": 1.2})
halo = [pe.withStroke(linewidth=4.0, foreground="white")]
prov = {}

# ------------------------------------------------------------------ data
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
Mc = M - 273.15
vmin, vmax = np.nanpercentile(Mc[land], [2, 98])
prov["window_km"] = [round((R - L) / 1000, 1), round((T - B) / 1000, 1)]
prov["p90_threshold_K"] = round(thr, 2)
prov["lst_colour_range_C"] = [round(float(vmin), 1), round(float(vmax), 1)]
hsj = json.load(open(P / "lst_exposure_indicators/hotspot_land_sensitivity.json"))
a, bl = hsj["A_published_all_grid"], hsj["B_pub_threshold_land_denominator"]
prov["hotspot"] = dict(window_ge1_pct=a["share_ge1_event_pct"], window_gt05_pct=a["share_f_gt_0p5_pct"],
                       land_ge1_pct=bl["share_ge1_event_pct"], land_gt05_pct=bl["share_f_gt_0p5_pct"],
                       f_max=a["f_max"], top_decile_cut=a["f_p90_top_decile_cut"])

df = pd.read_csv(SUHI)
df = df[df["lcz_class"].notna()].copy()
df["lcz_class"] = df["lcz_class"].astype(str)
df = df[~df["lcz_class"].isin(["0", "G", "nan", ""])].sort_values("suhi_intensity_K")
prov["suhi_K"] = dict(zip(df["lcz_class"], df["suhi_intensity_K"].round(2)))
prov["lczD_ref_K"] = float(df.loc[df["lcz_class"] == "D", "median_lst_K"].iloc[0])
prov["lcz8_median_K"] = float(df.loc[df["lcz_class"] == "8", "median_lst_K"].iloc[0])
conf = json.load(open(P / "lst_exposure_indicators/suhi_by_lcz/lcz_elevation_confound.json"))
prov["elev_matched_A_minus"] = {k: v["A_minus_ref_K"] for k, v in conf["cem_A_vs_built"].items()}

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)


def base(ax):
    ax.imshow(np.where(sea, 1.0, np.nan), extent=ext, cmap=ListedColormap([SEA]),
              interpolation="nearest", zorder=0)
    ax.set_xlim(L, R); ax.set_ylim(B, T); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_linewidth(1.2); sp.set_color("0.4")


def furniture(ax, labels=True):
    if labels:
        for name, (lat, lon) in PLACES.items():
            x, y = to_utm.transform(lon, lat)
            kw = dict(fontsize=FS, color="0.1", ha="center", va="center", zorder=6, path_effects=halo)
            if name == "Port":
                kw.update(ha="left"); x += 700; y -= 500
            if name == "Zona Franca":
                kw.update(ha="right"); x -= 300; y -= 300
            if name == "Collserola":
                kw.update(fontstyle="italic", color="#2e6b30")
            if name == "Barcelona":
                kw.update(fontweight="bold", color="#1b2a4a"); y += 900
            ax.text(x, y, name, **kw)
        sx, sy = to_utm.transform(2.214, 41.322)
        ax.text(sx, sy, "Mediterranean\nSea", fontsize=FS, fontstyle="italic",
                color="#3d6f99", ha="center", va="center", zorder=6, linespacing=1.0)
    sb_x, sb_y, sb_len = L + 900, B + 900, 5000
    ax.add_patch(Rectangle((sb_x, sb_y), sb_len / 2, 300, facecolor="black", zorder=7))
    ax.add_patch(Rectangle((sb_x + sb_len / 2, sb_y), sb_len / 2, 300, facecolor="white",
                           edgecolor="black", linewidth=1.0, zorder=7))
    ax.text(sb_x + sb_len / 2, sb_y + 500, "5 km", ha="center", va="bottom", fontsize=FS,
            zorder=7, path_effects=halo)
    nx, ny = R - 1300, T - 3600
    ax.annotate("", xy=(nx, ny + 2000), xytext=(nx, ny), zorder=7,
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=2.0, mutation_scale=25))
    ax.text(nx, ny + 2150, "N", ha="center", va="bottom", fontsize=FS, fontweight="bold",
            zorder=7, path_effects=halo)


def add_axes_cm(fig, x, y, w, h, W, H):
    return fig.add_axes([x / W, y / H, w / W, h / H])


# ------------------------------------------------------------------ figure 1: maps + SUHI
W, H = 76.0, 29.0
fig = plt.figure(figsize=(W * CM, H * CM))
map_h = 21.5
map_w = map_h * (R - L) / (T - B)
y0 = 5.0
# (c) census map: portrait, taller than (a)/(b) (it has no bottom colour bar), vertical bar right
g = gpd.read_file(CENSUS)
g["median_C"] = g["lst_median_30m_K"] - 273.15
gL, gB, gR, gT = g.total_bounds
pad = 250
gL, gB, gR, gT = gL - pad, gB - pad, gR + pad, gT + pad
c_h = map_h + y0 - 1.3                       # from 1.3 cm to the top of (a)/(b)
c_w = c_h * (gR - gL) / (gT - gB)
CBAR_W = 4.6                                  # vertical colour bar + ticks + label
gap_ab = (W - 0.6 - 2 * map_w - c_w - CBAR_W) / 2
xa = 0.3
xb = xa + map_w + gap_ab
a0 = add_axes_cm(fig, xa, y0, map_w, map_h, W, H)
a1 = add_axes_cm(fig, xb, y0, map_w, map_h, W, H)

base(a0)
im0 = a0.imshow(np.where(land, Mc, np.nan), extent=ext, cmap="RdYlBu_r", vmin=vmin, vmax=vmax,
                interpolation="nearest", zorder=1)
furniture(a0)
a0.set_title("(a) JJA median LST, 2013\u20132024", loc="left", fontsize=FS + 4,
             fontweight="bold", pad=12, y=1.0)
c0 = add_axes_cm(fig, xa + 1.0, 2.9, map_w - 2.0, 0.75, W, H)
cb0 = plt.colorbar(im0, cax=c0, orientation="horizontal", extend="both")
cb0.set_label("LST (\u00b0C)", fontsize=FS, labelpad=4)
cb0.ax.tick_params(labelsize=FS, length=6)

base(a1)
a1.imshow(np.where(land & (F == 0), 1.0, np.nan), extent=ext, cmap=ListedColormap([ZERO]),
          interpolation="nearest", zorder=1)
cmap_hs = ListedColormap(plt.get_cmap("YlOrRd")(np.linspace(0.15, 1.0, len(EDGES) - 1)))
im1 = a1.imshow(np.where(land & (F > 0), F, np.nan), extent=ext, cmap=cmap_hs,
                norm=BoundaryNorm(EDGES, cmap_hs.N), interpolation="nearest", zorder=2)
furniture(a1)
a1.set_title("(b) Hotspot frequency $f_{\\mathrm{hs}}$ (JJA)", loc="left", fontsize=FS + 4,
             fontweight="bold", pad=12, y=1.0)
c1 = add_axes_cm(fig, xb + 0.5, 2.9, map_w - 7.6, 0.75, W, H)
cb1 = plt.colorbar(im1, cax=c1, orientation="horizontal", spacing="proportional", ticks=EDGES)
cb1.ax.set_xticklabels(["0", ".1", ".2", ".29", ".5", ".7"])
cb1.ax.tick_params(labelsize=FS, length=6)
cb1.set_label(f"share of 153 scenes > P$_{{90}}$", fontsize=FS, labelpad=4)
fig.legend(handles=[Patch(facecolor=ZERO, edgecolor="0.4", label="never"),
                    Patch(facecolor=SEA, edgecolor="0.4", label="sea")],
           loc="lower left", bbox_to_anchor=((xb + map_w - 6.6) / W, 0.4 / H), frameon=False,
           fontsize=FS, handlelength=1.0, handleheight=0.9, labelspacing=0.25, borderaxespad=0)

# (c) building-buffer exposure by census section (Barcelona city)
xc = xb + map_w + gap_ab
a2 = add_axes_cm(fig, xc, 1.3, c_w, c_h, W, H)
cvmin, cvmax = np.nanpercentile(g["median_C"], [2, 98])
g.plot(column="median_C", ax=a2, cmap="inferno", vmin=cvmin, vmax=cvmax,
       edgecolor="0.55", linewidth=0.15)
g.dissolve(by="districte").boundary.plot(ax=a2, color="white", linewidth=1.6, alpha=0.9)
a2.set_xlim(gL, gR); a2.set_ylim(gB, gT); a2.set_aspect("equal"); a2.set_axis_off()
to_c = Transformer.from_crs("EPSG:4326", g.crs, always_xy=True)
for name, (lat, lon), dy in (("Eixample", (41.3920, 2.1640), 0), ("Zona Franca", (41.3430, 2.1450), -900),
                             ("Collserola", (41.4232, 2.1199), 0)):
    x, yv = to_c.transform(lon, lat)
    kw = dict(fontsize=FS, ha="center", va="center", color="0.1", path_effects=halo, zorder=5)
    if name == "Collserola":
        kw.update(fontstyle="italic", color="#2e6b30")
    a2.text(x, yv + dy, name, **kw)
sx, sy = gL + 700, gB + 700
a2.add_patch(Rectangle((sx, sy), 1000, 120, facecolor="black", zorder=7))
a2.add_patch(Rectangle((sx + 1000, sy), 1000, 120, facecolor="white", edgecolor="black",
                       linewidth=1.0, zorder=7))
a2.text(sx + 1000, sy + 250, "2 km", ha="center", va="bottom", fontsize=FS, path_effects=halo)
a2.set_title("(c) LST around buildings, by census section", loc="left", fontsize=FS + 4,
             fontweight="bold", pad=12, x=-0.02, y=1.0)
fig.canvas.draw()
for nm, ax_ in (("a", a0), ("b", a1), ("c", a2)):
    bb = ax_.get_position()
    print(f"[axes {nm}] x {bb.x0 * W:.1f}-{bb.x1 * W:.1f} cm, y {bb.y0 * H:.1f}-{bb.y1 * H:.1f} cm")
c2 = add_axes_cm(fig, xc + c_w + 0.5, 1.3 + 0.35 * c_h, 0.75, 0.6 * c_h, W, H)
sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(vmin=cvmin, vmax=cvmax))
cb2 = fig.colorbar(sm, cax=c2, extend="both",
                   ticks=np.arange(np.ceil(cvmin), cvmax + 0.01, 1.0))
cb2.ax.tick_params(labelsize=FS, length=6)
cb2.set_label("LST (\u00b0C)", fontsize=FS, labelpad=6)
prov["census_colour_range_C"] = [round(float(cvmin), 1), round(float(cvmax), 1)]
for ext_ in ("png", "pdf"):
    fig.savefig(OUT / f"fig_s5_maps.{ext_}", dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ figure 1b: compact SUHI by LCZ
# Column figure (poster middle column). Classes: the three cited in the abstract (8, 10, A),
# the reference (D) and the most extensive remaining classes (2, 5, 6, B). All 15 classes:
# paper, table "SUHI intensity by LCZ class" (tab:suhi) and Fig. fig:suhi.
KEEP = ["8", "10", "2", "D", "5", "6", "B", "A"]
df = df[df["lcz_class"].isin(KEEP)]
prov["suhi_compact_classes"] = KEEP
SUW, SUH = 25.0, 9.8
fig = plt.figure(figsize=(SUW * CM, SUH * CM))
a2 = add_axes_cm(fig, 9.0, 2.0, SUW - 9.2, SUH - 2.1, SUW, SUH)
vals = df["suhi_intensity_K"].values
labels = (df["lcz_class"] + "  " + df["description"].fillna("")).str.replace(
    "Bare soil or sand", "Bare soil").str.replace("Bare rock or paved", "Paved/rock").values
labels = [s + " (ref.)" if s.startswith("D ") else s for s in labels]
a2.barh(range(len(vals)), vals, color=[WARM if v >= 0 else COOL for v in vals],
        edgecolor="black", linewidth=0.8, height=0.72)
a2.set_yticks(range(len(vals)))
a2.set_yticklabels(labels, fontsize=FS)
for t in a2.get_yticklabels():
    if t.get_text().startswith("D "):
        t.set_fontweight("bold")
a2.axvline(0, color="black", linewidth=1.5)
a2.set_xlim(-10.2, 3.6)
a2.set_ylim(-0.6, len(vals) - 0.4)
a2.set_xticks([-8, -6, -4, -2, 0, 2])
a2.tick_params(axis="x", labelsize=FS, length=6)
a2.tick_params(axis="y", length=0)
a2.grid(axis="x", linestyle=":", alpha=0.5)
for i, v in enumerate(vals):
    if v == 0:
        continue
    a2.text(v + (0.15 if v > 0 else -0.15), i, f"{v:+.2f}", va="center",
            ha="left" if v > 0 else "right", fontsize=FS)
a2.set_xlabel("\u0394T vs LCZ D (K)", fontsize=FS, labelpad=2)
for s in ("top", "right"):
    a2.spines[s].set_visible(False)
for ext_ in ("png", "pdf"):
    fig.savefig(OUT / f"fig_s5_suhi.{ext_}", dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ driver model (numbers only)
rq3 = json.load(open(P / "rq3_drivers/rq3_ml_elevfix_results_land.json"))
cop = rq3["summary"]["copdem"]
prov["driver_model"] = dict(n=rq3["diagnostics"]["n"],
                            r2_mean_sd=[round(x, 2) for x in cop["test_r2_mean_sd"]],
                            rmse_mean_sd=[round(x, 2) for x in cop["test_rmse_mean_sd"]],
                            ols_r2_mean_sd=[round(x, 2) for x in cop["ols_r2_mean_sd"]],
                            ndvi_rank_per_seed=cop["ndvi_rank_per_seed"],
                            r_ndvi_lst=round(rq3["diagnostics"]["univariate_r_lst_ndvi"], 2),
                            shap_K={k: [round(v[0], 2), round(v[1], 2)]
                                    for k, v in cop["shap_mean_sd_K"].items()})

# ------------------------------------------------------------------ numbers for the text
era = json.load(open(P / "validation/validation_era5.json"))
eco = json.load(open(P / "validation/validation_ecostress.json"))
sc = eco["by_scene"]
prov["era5"] = dict(n=era["n_pairs"], bias=round(era["bias_K"], 2), rmse=round(era["rmse_K"], 2),
                    r=round(era["pearson_r"], 2),
                    by_season={s: dict(n=v["n_pairs"], bias=round(v["bias_K"], 2), r=round(v["pearson_r"], 2))
                               for s, v in era["by_season"].items()})
prov["ecostress"] = dict(n_scenes=eco["n_scenes"], n_px=eco["n_pixels"], bias=round(eco["bias_K"], 2),
                         rmse=round(eco["rmse_K"], 2), r=round(eco["pearson_r"], 2),
                         scene_bias_range=[round(min(s["bias_K"] for s in sc), 2),
                                           round(max(s["bias_K"] for s in sc), 2)],
                         scene_r_range=[round(min(s["pearson_r"] for s in sc), 2),
                                        round(max(s["pearson_r"] for s in sc), 2)],
                         bias_by_lcz={k: round(v["bias_K"], 2) for k, v in eco["by_lcz"].items()})
bld = pd.read_parquet(P / "lst_exposure_indicators/building_exposure/building_lst_exposure.parquet")
prov["buildings"] = dict(n=len(bld), municipalities=int(bld["municipality"].nunique()),
                         distinct_30m_medians=int(bld["lst_median_buffer_30m"].nunique()),
                         r_30_vs_100=round(float(bld[["lst_median_buffer_30m",
                                                      "lst_median_buffer_100m"]].corr().iloc[0, 1]), 3))
ct = pd.read_parquet(P / "lst_exposure_indicators/censustract_lst_exposure_clean.parquet")
med = ct["lst_median_30m_K"] - 273.15
prov["census"] = dict(n=len(ct), median_C_min_max=[round(med.min(), 1), round(med.max(), 1)],
                      median_C_iqr=[round(med.quantile(.25), 1), round(med.quantile(.75), 1)],
                      n_buildings_matched=int(ct["n_buildings"].sum()))
json.dump(prov, open(OUT / "fig_s5_provenance.json", "w"), indent=1, default=float)
print(json.dumps(prov, indent=1, default=float))
