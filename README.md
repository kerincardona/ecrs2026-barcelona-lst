# ECRS 2026 — Barcelona urban land surface temperature

Conference material for the **6th International Electronic Conference on Remote Sensing
(ECRS 2026)**, 19–21 October 2026, online (https://sciforum.net/event/ECRS2026).

Kerin Cardona, Jordi Cipriano, Gerard Mor — International Centre for Numerical Methods in
Engineering (CIMNE), Building Energy and Environment Group, Lleida, Spain.
Contact: kcardona@cimne.upc.edu

| Contribution | Session | Format | Files |
|---|---|---|---|
| Twelve-Year Landsat-Derived Surface Urban Heat Island Intensity by Local Climate Zone in Barcelona (2013–2024) | S5. Remote Sensing in Urban Areas | Oral + poster | `ecrs2026_presentation/talk/ECRS2026_talk_S5.pdf`, `conference/ECRS2026/ECRS2026_poster_S5.pdf` |
| Towards a Spatio-Temporally Complete Urban Land Surface Temperature Record: A Multi-Sensor Benchmark and Rank-Based Baseline Evaluation for Thermal Downscaling over Barcelona | S1. AI in Remote Sensing | Poster | `conference/ECRS2026/ECRS2026_poster_S1.pdf` |

Accepted abstracts: `abstracts/`.

## Contents

```
abstracts/                    accepted abstracts (plain text, as submitted)
conference/ECRS2026/          posters (pptx/pdf/png), poster builders, print-size figures,
                              *_provenance.json = every number quoted on the posters
ecrs2026_presentation/        oral talk: Beamer deck (talk/),
                              figures/ (slide figures, conference banner)
scripts/                      figure scripts for the posters and the slides
```

## Rebuilding

Requirements: Python ≥ 3.10 (`pip install -r requirements.txt`), LibreOffice (pptx → pdf),
poppler (`pdfinfo`, `pdftoppm`), a LaTeX distribution with Beamer and TikZ.

- **Talk:** `cd ecrs2026_presentation/talk && latexmk -pdf ECRS2026_talk_S5.tex`
- **Posters:** download the official poster template from the ECRS 2026
  *Instructions for Authors* page (`2026-Poster-Template.pptx`), save it as
  `conference/ECRS2026/templates/2026-Poster-Template.pptx`, then run
  `conference/ECRS2026/render_poster_s5.sh` or `render_poster.sh`.
  Set `SOFFICE=/path/to/soffice` if LibreOffice is not in the macOS default location.

The posters rebuild from the figures and provenance files committed here. **Regenerating the
figures** (`scripts/`) requires the processed Landsat / Sentinel-3 / ECOSTRESS products
under `data/`, which are not part of this repository; the scripts document their inputs in
their headers.

## Data sources

Landsat 8/9 Collection 2 Level-2 (USGS, via Microsoft Planetary Computer); Sentinel-3 SLSTR
(Copernicus); ECOSTRESS L2G LSTE v002 (NASA LP DAAC); ERA5-Land (Copernicus Climate Change
Service); global LCZ map (Demuzere et al., 2019); INSPIRE cadastral buildings; Copernicus
GLO-30 DEM, High Resolution Layer imperviousness and Urban Atlas; Barcelona census sections
(Ajuntament de Barcelona).

The ECRS 2026 banner and poster template belong to the conference organisers (MDPI / Sciforum).

## Licence

- **Code** (`*.py`, `*.sh`, the LaTeX source of the deck): MIT — see `LICENSE`.
- **Content** (posters, slides, figures, abstracts, provenance JSON): Creative Commons
  Attribution 4.0 International (CC BY 4.0) — see `LICENSE-CC-BY-4.0.txt`.
  Please cite as: Cardona K., Cipriano J., Mor G. (2026). ECRS 2026, Sciforum/MDPI.
- **Not covered by either licence:** the ECRS 2026 banner
  (`ecrs2026_presentation/figures/branding/`) and the graphic elements of the official poster
  template embedded in the posters (header, logos, footer), which remain property of
  MDPI / Sciforum. Underlying satellite and ancillary data keep their own licences
  (see *Data sources*).
