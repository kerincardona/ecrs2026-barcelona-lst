#!/usr/bin/env bash
# Build + render the ECRS2026 S1 poster (Abstract 2, benchmark): pptx -> pdf -> png preview.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
SOFFICE=${SOFFICE:-/Applications/LibreOffice.app/Contents/MacOS/soffice}
N=ECRS2026_poster_S1_official_template
"$PY" build_poster_pptx.py
rm -f $N.pdf $N.png
"$SOFFICE" --headless --convert-to pdf $N.pptx >/dev/null 2>&1
pdfinfo $N.pdf | grep -E "Pages|Page size"
pdftoppm -r 60 -png -singlefile $N.pdf $N
