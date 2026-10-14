#!/usr/bin/env python3
"""ECRS 2026 deck v2, slide 3: study-area context map (complete version).

Replaces the v1 placeholder (bbox outline over a flat fill). Adds:
  - light basemap (CARTO Voyager, no labels) for geographic context,
  - AOI = the actual 30 m analysis grid extent, read from the LST raster
    (not the WGS84 bbox, whose UTM projection is slightly skewed),
  - dimmed area outside the AOI, a few place labels (geocoded with Nominatim,
    coordinates stored below), scale bar, north arrow, Iberia locator inset.

Area and dimensions are computed from the raster grid: nothing hard-coded.

Basemap tiles are fetched once with contextily and cached as GeoTIFFs in
ecrs2026_presentation/figures/_basemap/; later runs need neither network
nor contextily.

Output: ecrs2026_presentation/figures/fig_studyarea_v2.{pdf,png}
Run:    .venv/bin/python scripts/make_fig_studyarea_v2.py
        (first run only: contextily importable, e.g. PYTHONPATH=<dir with contextily>)
"""
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path as MplPath

REPO = Path(__file__).resolve().parent.parent
LST_TIF = REPO / "data/processed/lst_climatology_AMB_2013-2024/lst_median_JJA_daytime.tif"
OUT_DIR = REPO / "ecrs2026_presentation/figures"
CACHE = OUT_DIR / "_basemap"
CACHE.mkdir(parents=True, exist_ok=True)
OUT_PDF = OUT_DIR / "fig_studyarea_v2.pdf"
OUT_PNG = OUT_DIR / "fig_studyarea_v2.png"

UTM = "EPSG:32631"
WARM = "#c0392b"
NAVY = "#1b2a4a"

# Place labels, (lat, lon) from OSM Nominatim (queried 2026-10-08).
PLACES = {
    "Barcelona":       (41.3826, 2.1771),
    "L'Hospitalet":    (41.3595, 2.0996),
    "Badalona":        (41.4494, 2.2483),
    "El Prat":         (41.3306, 2.0931),
    "Sant Cugat":      (41.4708, 2.0849),
    "Collserola":      (41.4232, 2.1199),   # Tibidabo summit
}

# ---------------------------------------------------------------- AOI (grid)
with rasterio.open(LST_TIF) as src:
    assert src.crs.to_string() == UTM, src.crs
    L, B, R, T = src.bounds
w_km, h_km = (R - L) / 1e3, (T - B) / 1e3
area_km2 = w_km * h_km

pad = 4500.0  # m around the AOI (west, south, north)
pad_east = 11500.0  # wider sea margin on the east for the locator inset
X0, X1, Y0, Y1 = L - pad, R + pad_east, B - pad, T + pad


def cached_basemap(name, source, bounds_utm, zoom, dst_crs=UTM):
    """Return (array RGB, extent) of a basemap warped to dst_crs, cached on disk."""
    out = CACHE / f"{name}_{dst_crs.replace(':', '')}.tif"
    if not out.exists():
        import contextily as cx  # only needed on first run
        w, s, e, n = transform_bounds(dst_crs, "EPSG:4326", *bounds_utm, densify_pts=21)
        raw = CACHE / f"{name}_3857.tif"
        cx.bounds2raster(w, s, e, n, str(raw), zoom=zoom, source=source, ll=True)
        with rasterio.open(raw) as s3857:
            tr, wd, ht = calculate_default_transform(s3857.crs, dst_crs, s3857.width,
                                                     s3857.height, *s3857.bounds)
            prof = s3857.profile.copy()
            prof.update(crs=dst_crs, transform=tr, width=wd, height=ht, driver="GTiff",
                        compress="deflate")
            with rasterio.open(out, "w", **prof) as dst:
                for b in range(1, s3857.count + 1):
                    reproject(rasterio.band(s3857, b), rasterio.band(dst, b),
                              resampling=Resampling.bilinear)
        raw.unlink()
    with rasterio.open(out) as s:
        arr = s.read([1, 2, 3])
        b = s.bounds
    return np.moveaxis(arr, 0, -1), (b.left, b.right, b.bottom, b.top)


def provider(name):
    import contextily as cx
    # CARTO tiles now require an API key -> Esri Light Gray Base (no labels, keyless).
    return {"graycanvas": cx.providers.Esri.WorldGrayCanvas}[name]


def get(name, prov, bounds, zoom, crs=UTM):
    out = CACHE / f"{name}_{crs.replace(':', '')}.tif"
    return cached_basemap(name, None if out.exists() else provider(prov), bounds, zoom, crs)


halo = [pe.withStroke(linewidth=2.2, foreground="white")]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5})

FIG_H = 3.4
fig = plt.figure(figsize=(FIG_H * (X1 - X0) / (Y1 - Y0), FIG_H))
ax = fig.add_axes([0, 0, 1, 1])

img, ext = get("aoi_graycanvas_z12_e11k", "graycanvas", (X0, Y0, X1, Y1), 12)
ax.imshow(img, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
ax.set_xlim(X0, X1)
ax.set_ylim(Y0, Y1)
ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_linewidth(0.6); sp.set_color("0.4")

# Dim everything outside the AOI (outer rectangle minus inner rectangle).
outer = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0)]
inner = [(L, B), (L, T), (R, T), (R, B), (L, B)]   # opposite winding -> hole
codes = [MplPath.MOVETO] + [MplPath.LINETO] * 3 + [MplPath.CLOSEPOLY]
ax.add_patch(PathPatch(MplPath(outer + inner, codes + codes), facecolor="white",
                       edgecolor="none", alpha=0.55, zorder=1))
ax.add_patch(Rectangle((L, B), R - L, T - B, fill=False, edgecolor=WARM,
                       linewidth=1.6, zorder=3))

# Place labels.
to_utm = Transformer.from_crs("EPSG:4326", UTM, always_xy=True)
for name, (lat, lon) in PLACES.items():
    x, y = to_utm.transform(lon, lat)
    if name == "Badalona":  # centroid sits on the AOI edge; nudge label inside
        x -= 1500
    style = dict(fontsize=8.5, color="0.15", ha="center", va="center", zorder=5,
                 path_effects=halo)
    if name == "Barcelona":
        style.update(fontsize=10.5, fontweight="bold", color=NAVY)
    if name == "Collserola":
        style.update(fontstyle="italic", color="#2e6b30")
    ax.text(x, y, name, **style)

# Sea label (open water south-east of the coast).
sx, sy = to_utm.transform(2.318, 41.372)
ax.text(sx, sy, "Mediterranean\nSea", fontsize=8, fontstyle="italic", color="#3d6f99",
        ha="center", va="center", zorder=5, linespacing=1.0)

# AOI dimensions as edge annotations (outside the box, in the dimmed margin).
ax.text((L + R) / 2, T + 700, f"{w_km:.1f} km", ha="center", va="bottom",
        fontsize=8, color=WARM, fontweight="bold", zorder=6, path_effects=halo)
ax.text(L - 700, (B + T) / 2, f"{h_km:.1f} km", ha="right", va="center", rotation=90,
        fontsize=8, color=WARM, fontweight="bold", zorder=6, path_effects=halo)

# Scale bar (UTM metres, exact) bottom-left.
sb_x, sb_y, sb_len = X0 + 1500, Y0 + 1500, 5000
ax.add_patch(Rectangle((sb_x, sb_y), sb_len / 2, 250, facecolor="black", zorder=6))
ax.add_patch(Rectangle((sb_x + sb_len / 2, sb_y), sb_len / 2, 250, facecolor="white",
                       edgecolor="black", linewidth=0.5, zorder=6))
ax.text(sb_x + sb_len / 2, sb_y + 450, "5 km", ha="center", va="bottom", fontsize=6.5,
        zorder=6, path_effects=halo)

# North arrow (grid north; convergence at 2.1°E in UTM 31N is < 0.6°).
nx, ny = X1 - 1600, Y1 - 3300
ax.annotate("", xy=(nx, ny + 1900), xytext=(nx, ny), zorder=6,
            arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.0,
                            mutation_scale=8))
ax.text(nx, ny + 2050, "N", ha="center", va="bottom", fontsize=7.5, fontweight="bold",
        zorder=6, path_effects=halo)

# Attribution.
ax.text(X0 + 300, Y1 - 250, "Basemap: Esri Light Gray Canvas", fontsize=4.5,
        ha="left", va="top", color="0.35", zorder=6)

# ------------------------------------------------------- Iberia locator inset
ib_ll = (-9.8, 35.8, 4.6, 44.0)  # lon/lat
tf_inset = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
ix0, iy0 = tf_inset.transform(ib_ll[0], ib_ll[1])
ix1, iy1 = tf_inset.transform(ib_ll[2], ib_ll[3])
ins_img, ins_ext = get("iberia_graycanvas_z5", "graycanvas", (ix0, iy0, ix1, iy1), 5,
                       crs="EPSG:3857")
iax = fig.add_axes([0.745, 0.06, 0.235, 0.235])
iax.imshow(ins_img, extent=ins_ext, origin="upper", zorder=0)
iax.set_xlim(ix0, ix1); iax.set_ylim(iy0, iy1)
iax.set_xticks([]); iax.set_yticks([])
for sp in iax.spines.values():
    sp.set_linewidth(0.6); sp.set_color("0.4")
bx, by = tf_inset.transform(2.125, 41.40)
iax.plot(bx, by, marker="s", markersize=4.5, markerfacecolor="none",
         markeredgecolor=WARM, markeredgewidth=1.4, zorder=3)

fig.savefig(OUT_PDF, dpi=300)
fig.savefig(OUT_PNG, dpi=300)
print(f"AOI grid: {w_km:.2f} x {h_km:.2f} km = {area_km2:.1f} km2")
print(f"Saved {OUT_PDF}\nSaved {OUT_PNG}")
