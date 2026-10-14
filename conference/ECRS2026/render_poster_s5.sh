#!/usr/bin/env bash
# Build + render the ECRS2026 S5 poster (Abstract 1, SUHI by LCZ): figures -> pptx -> pdf -> png.
# Figures are regenerated only if the processed data are present under ../../data/processed
# (not included in this repository); otherwise the committed fig_s5_* files are used.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
SOFFICE=${SOFFICE:-/Applications/LibreOffice.app/Contents/MacOS/soffice}
N=ECRS2026_poster_S5_v1
if [ -d ../../data/processed ]; then "$PY" ../../scripts/figure_poster_s5.py > /dev/null; fi
"$PY" build_poster_s5_pptx.py
rm -f $N.pdf $N.png
"$SOFFICE" --headless --convert-to pdf $N.pptx >/dev/null 2>&1
pdfinfo $N.pdf | grep -E "Pages|Page size"
pdftoppm -r 60 -png -singlefile $N.pdf $N
