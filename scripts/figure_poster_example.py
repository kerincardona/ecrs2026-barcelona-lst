#!/usr/bin/env python3
"""Figura de 3 paneles para el poster ECRS 2026 (S1, benchmark S3->L8).

Muestra, para UNA fecha del split de test, la cadena completa del argumento:

    (a) Sentinel-3 nativo (1 km, remuestreado al grid 30 m)  -> Baseline 1
    (b) Baseline 3 = climatologia L8 (train) + anomalia S3 del dia
    (c) Landsat real (30 m) = verdad de terreno

Replica EXACTAMENTE la formulacion de B3 de scripts/evaluate_baselines.py:
    s3_clim = nanmean(s3_train, axis=0)
    l8_clim = nanmean(l8_train, axis=0)
    pred    = l8_clim + (s3_test[i] - s3_clim)

Split identico al benchmark: train 2016-2021, val 2022, test 2023-2024.
La climatologia se calcula SOLO con train (sin fuga hacia el test).

Uso:
    .venv/bin/python scripts/figure_poster_example.py --date 2024-08-03
"""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from scipy import stats

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parent.parent
PAIRED_ZARR = REPO_ROOT / "data/interim/paired_s3_l8/paired_s3_l8.zarr"
OUT_DIR = REPO_ROOT / "conference/ECRS2026"
LCZ_GEOREF = REPO_ROOT / "data/interim/paired_s3_l8/baselines/lcz_on_paired_grid_georef.npy"

# Mismo split que scripts/evaluate_baselines.py
TRAIN_YEARS = (2016, 2021)
TEST_YEARS = (2023, 2024)


def spearman_valid(pred, target):
    """Spearman sobre pixeles validos en ambos campos."""
    p = pred.ravel()
    t = target.ravel()
    ok = np.isfinite(p) & np.isfinite(t)
    if ok.sum() < 100:
        return np.nan, int(ok.sum())
    rho, _ = stats.spearmanr(p[ok], t[ok])
    return float(rho), int(ok.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2024-08-03",
                    help="fecha del split de test a graficar (YYYY-MM-DD)")
    ap.add_argument("--out", default="fig_poster_example",
                    help="nombre base de salida (sin extension)")
    ap.add_argument("--print-width-cm", type=float, default=None,
                    help="modo poster: figsize = ancho fisico final en el A0, de modo que "
                         "los tamanos de fuente en pt sean los impresos (>=24 pt), sin "
                         "suptitle (el pie del poster ya lo dice) y PNG a 300 dpi")
    ap.add_argument("--with-b2", action="store_true",
                    help="anade panel B2 (media LST train por LCZ) con el LCZ "
                         "GEORREFERENCIADO de scripts/qa_b2_lcz_registration.py")
    args = ap.parse_args()

    print(f"[1] Abriendo {PAIRED_ZARR}")
    ds = xr.open_zarr(PAIRED_ZARR)
    s3 = ds["s3_lst"].values  # (time, y, x), grados C
    l8 = ds["l8_lst"].values
    dates = ds.time.values
    years = np.array([int(str(d)[:4]) for d in dates])

    train_mask = (years >= TRAIN_YEARS[0]) & (years <= TRAIN_YEARS[1])
    test_mask = (years >= TEST_YEARS[0]) & (years <= TEST_YEARS[1])
    print(f"    train: {train_mask.sum()} fechas | test: {test_mask.sum()} fechas")

    # Fecha objetivo dentro del test
    date_strs = np.array([str(d)[:10] for d in dates])
    hits = np.where((date_strs == args.date) & test_mask)[0]
    if len(hits) == 0:
        avail = sorted(date_strs[test_mask])
        raise SystemExit(
            f"Fecha {args.date} no esta en el split de test.\n"
            f"Disponibles ({len(avail)}): {avail}"
        )
    t_idx = int(hits[0])
    print(f"[2] Fecha objetivo: {args.date} (indice {t_idx})")

    # Climatologias SOLO con train  (identico a baseline_climatology_offset)
    print("[3] Climatologia train-only (sin fuga al test)")
    s3_clim = np.nanmean(s3[train_mask], axis=0)
    l8_clim = np.nanmean(l8[train_mask], axis=0)

    s3_day = s3[t_idx]
    l8_day = l8[t_idx]
    b3_pred = l8_clim + (s3_day - s3_clim)

    # Metricas de esta escena (para el pie de figura)
    rho_b1, n_b1 = spearman_valid(s3_day, l8_day)
    rho_b3, n_b3 = spearman_valid(b3_pred, l8_day)
    print(f"[4] Spearman esta escena -> S3 nativo: {rho_b1:.3f} | B3: {rho_b3:.3f}")
    b2_pred, rho_b2 = None, None
    if args.with_b2:
        lcz = np.load(LCZ_GEOREF)
        l8_train = l8[train_mask]
        b2_pred = np.full(l8_day.shape, np.nan, dtype=np.float32)
        for c in [c for c in np.unique(lcz) if c > 0]:
            b2_pred[lcz == c] = np.nanmean(l8_train[:, lcz == c])
        rho_b2, _ = spearman_valid(b2_pred, l8_day)
        print(f"    B2 (LCZ georef): {rho_b2:.3f}")

    # Escala de color: (b) y (c) comparten la escala del campo verdadero.
    # (a) Sentinel-3 necesita SU PROPIA escala: ese dia el campo de 1 km vive en
    # ~20-24 C mientras Landsat cubre ~26-57 C, asi que forzar una escala comun
    # lo dejaria saturado en negro y ocultaria que si tiene textura (gruesa).
    finite_truth = l8_day[np.isfinite(l8_day)]
    vmin, vmax = np.percentile(finite_truth, [2, 98])
    finite_s3 = s3_day[np.isfinite(s3_day)]
    s3_vmin, s3_vmax = np.percentile(finite_s3, [2, 98])
    print(f"[5] Escala (b)(c): {vmin:.1f} - {vmax:.1f} C")
    print(f"    Escala (a) S3 : {s3_vmin:.1f} - {s3_vmax:.1f} C  "
          f"(rango dinamico {s3_vmax - s3_vmin:.1f} K vs {vmax - vmin:.1f} K)")

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    s3_norm = mcolors.Normalize(vmin=s3_vmin, vmax=s3_vmax)
    cmap = plt.get_cmap("inferno").copy()
    cmap.set_bad("#d9d9d9")  # nubes / sin dato

    # s3_lst en el zarr es SLSTR S8 (10.8 um) = temperatura de brillo, no LST
    # (attrs del zarr: source 'Sentinel-3 SLSTR S8 (10.8um)').
    poster = args.print_width_cm is not None
    if poster:
        fs_title, fs_sub, fs_cbar, fs_tick = 32, 26, 26, 24
        aspect = 0.33 if args.with_b2 else 0.43
        figsize = (args.print_width_cm / 2.54, args.print_width_cm / 2.54 * aspect)
    else:
        fs_title, fs_sub, fs_cbar, fs_tick = 14, 11, 11, 10
        figsize = (13.5, 5.0)

    panels = [
        (s3_day, s3_norm, "(a) Sentinel-3 S8 BT (1 km)",
         (f"own scale  |  $\\rho$ = {rho_b1:.2f}" if poster else
          f"own scale {s3_vmin:.0f}-{s3_vmax:.0f}$^\\circ$C  |  $\\rho$ = {rho_b1:.2f}")),
        (b3_pred, norm, "(b) Baseline 3 (30 m)",
         (f"$\\rho$ = {rho_b3:.2f}" if poster else
          f"climatology + S3 anomaly  |  $\\rho$ = {rho_b3:.2f}")),
        (l8_day, norm, "(c) Landsat truth (30 m)",
         "reference"),
    ]
    if args.with_b2:
        # B2 = media de TODO el train (todas las estaciones): en un dia de agosto
        # queda ~10 K por debajo y en la escala Landsat se ve negro. Escala propia
        # para mostrar su estructura (bloques LCZ); el sesgo ya esta en la tabla.
        b2_vmin, b2_vmax = np.nanpercentile(b2_pred, [2, 98])
        b2_norm = mcolors.Normalize(vmin=b2_vmin, vmax=b2_vmax)
        print(f"    Escala (b) B2 : {b2_vmin:.1f} - {b2_vmax:.1f} C")
        panels = [
            (s3_day, s3_norm, "(a) Sentinel-3 S8 BT (1 km)", f"own scale  |  $\\rho$ = {rho_b1:.2f}"),
            (b2_pred, b2_norm, "(b) B2: mean per LCZ", f"own scale  |  $\\rho$ = {rho_b2:.2f}"),
            (b3_pred, norm, "(c) B3: clim. + anomaly", f"$\\rho$ = {rho_b3:.2f}"),
            (l8_day, norm, "(d) Landsat truth (30 m)", "reference"),
        ]

    fig, axes = plt.subplots(1, len(panels), figsize=figsize, constrained_layout=True)
    ims = []
    for ax, (field, pnorm, title, sub) in zip(axes, panels):
        im = ax.imshow(np.ma.masked_invalid(field), cmap=cmap, norm=pnorm,
                       interpolation="nearest")
        ims.append(im)
        ax.set_title(title, fontsize=fs_title, fontweight="bold", pad=8)
        ax.set_xlabel(sub, fontsize=fs_sub)
        ax.set_xticks([])
        ax.set_yticks([])

    # Barra propia para (a), barra compartida para (b)+(c)
    cbar_a = fig.colorbar(ims[0], ax=axes[0], fraction=0.046, pad=0.02,
                          location="bottom")
    cbar_a.set_label("S3 brightness temp. ($^\\circ$C)", fontsize=fs_cbar)
    cbar_a.ax.tick_params(labelsize=fs_tick)
    if args.with_b2:
        cbar_b2 = fig.colorbar(ims[1], ax=axes[1], fraction=0.046, pad=0.02,
                               location="bottom")
        cbar_b2.set_label("B2 LST ($^\\circ$C)", fontsize=fs_cbar)
        cbar_b2.ax.tick_params(labelsize=fs_tick)
        from matplotlib.ticker import MaxNLocator
        cbar_b2.ax.xaxis.set_major_locator(MaxNLocator(4))
    shared = list(axes[2:]) if args.with_b2 else list(axes[1:])
    cbar_bc = fig.colorbar(ims[-1], ax=shared, fraction=0.046,
                           pad=0.02, location="bottom")
    cbar_bc.set_label("LST ($^\\circ$C)", fontsize=fs_cbar)
    cbar_bc.ax.tick_params(labelsize=fs_tick)

    if poster:
        from matplotlib.ticker import MaxNLocator
        for cb in (cbar_a, cbar_bc):
            cb.ax.xaxis.set_major_locator(MaxNLocator(4))
    else:
        fig.suptitle(
            f"Held-out test date {args.date} — the 1 km field spans only "
            f"{s3_vmax - s3_vmin:.0f} K against Landsat's {vmax - vmin:.0f} K: "
            f"no fine structure to resample; the prior supplies it",
            fontsize=12,
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / f"{args.out}.png"
    pdf = OUT_DIR / f"{args.out}.pdf"
    fig.savefig(png, dpi=300 if poster else 200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print(f"[6] Guardado: {png}")
    print(f"           {pdf}")

    # Provenance versionable (mismo patron que validation_*.json)
    prov = {
        "figure": f"{args.out}.png",
        "date": args.date,
        "time_index": t_idx,
        "split": {
            "train_years": list(TRAIN_YEARS),
            "test_years": list(TEST_YEARS),
            "n_train_dates": int(train_mask.sum()),
            "n_test_dates": int(test_mask.sum()),
        },
        "baseline3_formulation": "l8_clim(train) + (s3_day - s3_clim(train))",
        "scene_spearman": {
            "s3_native_vs_landsat": rho_b1,
            "baseline3_vs_landsat": rho_b3,
            "baseline2_lcz_georef_vs_landsat": rho_b2,
            "n_valid_px_s3": n_b1,
            "n_valid_px_b3": n_b3,
        },
        "colour_scale_C": {
            "panels_bc": {"vmin": float(vmin), "vmax": float(vmax),
                          "rule": "robust 2-98 percentile of Landsat truth"},
            "panel_a_s3": {"vmin": float(s3_vmin), "vmax": float(s3_vmax),
                           "rule": "own 2-98 percentile; S3 occupies a different "
                                   "absolute range and would saturate on the "
                                   "Landsat scale"},
        },
        "dynamic_range_K": {
            "sentinel3_1km": float(s3_vmax - s3_vmin),
            "landsat_30m": float(vmax - vmin),
            "note": ("dynamic range of the scene; the 1 km field cannot carry 30 m detail "
                     "(the old 'nearly flat' note described the NIGHT-pass S3)"),
        },
        "source_zarr": str(PAIRED_ZARR.relative_to(REPO_ROOT)),
        "note": ("Per-scene Spearman; the poster table reports the mean over the "
                 "61 held-out test pairs, so these values differ from it."),
    }
    prov_path = OUT_DIR / f"{args.out}_provenance.json"
    prov_path.write_text(json.dumps(prov, indent=2))
    print(f"[7] Provenance: {prov_path}")


if __name__ == "__main__":
    main()
