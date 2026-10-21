# LinkedIn post — ECRS 2026 (English)

Status: drafted 2026-10-21, not yet published.

---

Presented today at the 6th International Electronic Conference on Remote Sensing (ECRS 2026, MDPI/Sciforum) — two contributions on Barcelona's urban thermal environment.

Oral talk (Session S5, Remote Sensing in Urban Areas):
"Twelve-Year Landsat-Derived Surface Urban Heat Island Intensity by Local Climate Zone in Barcelona (2013-2024)"

We built a 12-year, 30 m land surface temperature (LST) climatology over 464 km² of metropolitan Barcelona from 378 Landsat 8/9 scenes, and quantified Surface Urban Heat Island (SUHI) intensity by Local Climate Zone (Bechtel et al., 2019).

Key results:
→ Large low-rise zones (LCZ 8) reach the highest summer LST (316.4 K), +1.4 K above the rural reference; heavy industry (LCZ 10) follows (+1.0 K); dense tree cover (LCZ A) is 8.0 K cooler.
→ 64% of the study area experiences at least one hotspot event; 1.1% is persistently affected.
→ Cross-validation: ERA5-Land tracks the pooled seasonal cycle (r=0.92) but not intra-urban structure (r=0.26), as expected for a 0.1° reanalysis; ECOSTRESS (70 m) is consistent with the Landsat field (bias +0.37 K, RMSE 4.4 K, r=0.92).

Outcome: a reproducible thermal-exposure baseline for 106,000+ buildings across 13 municipalities — a direct input for urban climate adaptation planning in Mediterranean coastal cities.

Poster (Session S1, AI in Remote Sensing):
"Towards a Spatio-Temporally Complete Urban LST Record: A Multi-Sensor Benchmark and Rank-Based Baseline Evaluation for Thermal Downscaling over Barcelona"

No single sensor delivers high-resolution LST completely — Landsat is ~100 m/16-day revisit, Sentinel-3 is daily at 1 km, ECOSTRESS is 70 m but irregular. We introduce a rank-based benchmark (137 co-registered Sentinel-3/Landsat pairs, 2016-2024, temporally split train/val/test) and three baselines on 61 held-out pairs:
→ Naive resampling of coarse Sentinel-3 fails as expected (Spearman -0.06) — resampling isn't downscaling.
→ A per-pixel Landsat climatology corrected by Sentinel-3's daily anomaly performs best (Spearman 0.74, hotspot F1 0.24, RMSE 4.7 K), consistent against independent ECOSTRESS (Spearman 0.83).
→ Takeaway: any learned downscaling model must beat this climatological prior to add real value — and the residual is temporal, not static-covariate.

Joint work with Jordi Cipriano and Gerard Mor (CIMNE, Building Energy and Environment Group).

All material — slides, posters, abstracts, code and provenance — is open here:
https://github.com/kerincardona/ecrs2026-barcelona-lst

#RemoteSensing #UrbanHeatIsland #ClimateAdaptation #Landsat #ECOSTRESS #Sentinel3 #UrbanClimate #ECRS2026
