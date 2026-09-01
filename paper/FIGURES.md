# Figure sources and exports

Figures 1--4 are TikZ inside `crossaudit.tex`. Figures 5--6 are generated with
Python/Matplotlib from the sealed v4 feasibility summary and included as vector
PDFs with `\includegraphics`. Their PDFs under `paper/figures/` are therefore
required paper-build inputs; their SVG/PNG/TIFF siblings are publication and
preview exports. The graphical abstracts and standalone protocol export remain
optional portal/README assets.

| Source | Tracked outputs | Role |
|---|---|---|
| `crossaudit.tex` | `crossaudit-paper.pdf` | The paper (24 pp, 6 figures, 4 tables, and 22 references in the current v2 candidate; published v1 was 19 pp). `crossaudit.pdf` is the raw build product and is gitignored; the tracked record is the `-paper` name. |
| `../experiment/v4/figures/plot_feasibility.py` | `figures/figure5-v4-configuration-effects.{pdf,svg,png,tiff}`, `figures/figure6-v4-operational-tradeoffs.{pdf,svg,png,tiff}`, and `../experiment/v4/figures/source-data.csv` | Python-only, data-bound sources for in-paper Figures 5--6. The script reads the sealed Amendment 2 `summary.json`, asserts its freeze/completion contract, and runs the `nature-figure` 1.5 pt Matplotlib alignment gate before export. The two PDFs are build inputs; the other formats are exports. |
| `../experiment/v4/figures/run_qa.py` | `../experiment/v4/figures/qa/` and `../experiment/v4/figures/QA-NOTES.md` | Re-runs the `nature-figure` source preflight, 5 pt rendered-text floor, strict PDF collision audit, and alignment-result checks. `qa/qa-summary.json` is the machine-readable aggregate; `QA-NOTES.md` records panel-by-panel and compiled-paper inspection. |
| `crossaudit-abstract-figure.tex` | `crossaudit-abstract-figure.pdf`, `.png` | Graphical abstract, **results-oriented**: problem → protocol → seeded-defect outcome, with the permutation floors as bar rules. Floors come from `experiment/results/NULLCHECK.json`; when those numbers change, this figure changes (see R1 in `audits/2026-07-31-sixth-audit-dispositions.md`). |
| `graphical-abstract-v2.tex` | `crossaudit-graphical-abstract-v2.pdf`, `.png` | Graphical abstract, **protocol-oriented** (three-column loop). Submission-portal variant; carries no result numbers, so it does not depend on NULLCHECK. Supersedes the v1 `graphical-abstract.tex` family, removed from the tree 2026-07-31. |
| `figure1-standalone.tex` | `figure1-standalone.pdf`, `crossaudit-figure1.png` | The clockwise protocol ring as a standalone export; its current in-paper copy is Figure 2 and is drawn by `crossaudit.tex` itself. |
| `../diagrams/architecture.mmd` | `../diagrams/architecture.png`, `.svg` | Repository architecture (Mermaid). Canonical copy; the WeChat article references this path rather than carrying its byte-identical twin (removed 2026-07-31). |

## Regenerating

```bash
# From the repository root: regenerate the two quantitative figures.
# Install nature-figure/nature-shared from https://github.com/Yuan1z0825/nature-skills
# at ebd722e18808442688bd205917a3e774195c258f first, or point
# NATURE_FIGURE_SKILL_ROOT at the installed nature-figure skill.
uv run --no-project --python 3.12 \
  --with-requirements experiment/v4/figures/requirements.txt \
  python experiment/v4/figures/plot_feasibility.py

# Run the source, rendered-text, alignment, and strict collision QA gates.
uv run --no-project --python 3.12 \
  --with-requirements experiment/v4/figures/requirements.txt \
  python experiment/v4/figures/run_qa.py

# Build the paper twice for cross-references, then refresh the tracked record.
cd paper
pdflatex -halt-on-error -interaction=nonstopmode crossaudit.tex
pdflatex -halt-on-error -interaction=nonstopmode crossaudit.tex
cp crossaudit.pdf crossaudit-paper.pdf

# standalone figures: compile, then export PNG from the PDF
pdflatex -interaction=nonstopmode crossaudit-abstract-figure.tex
pdftoppm -png -r 600 -singlefile crossaudit-abstract-figure.pdf crossaudit-abstract-figure

pdflatex -interaction=nonstopmode graphical-abstract-v2.tex   # -> graphical-abstract-v2.pdf
# tracked under the crossaudit- prefix:
mv graphical-abstract-v2.pdf crossaudit-graphical-abstract-v2.pdf
pdftoppm -png -r 300 -singlefile crossaudit-graphical-abstract-v2.pdf crossaudit-graphical-abstract-v2

pdflatex -interaction=nonstopmode figure1-standalone.tex
pdftoppm -png -r 300 -singlefile figure1-standalone.pdf crossaudit-figure1
```

The current QA record reports source preflight PASS, 1.5 pt alignment PASS,
strict collision PASS, and a 6.0 pt minimum rendered glyph size for both Python
figures. Any change to data, plotting code, text, fonts, annotations, or layout
requires rerunning both commands and inspecting every panel at final paper size.
The QA-only alignment overlays must never replace the submission PDFs.

CI stages only the arXiv `main.tex` plus the two required PDFs in a clean
temporary source tree, verifies that `main.tex` matches `crossaudit.tex`,
compiles three times, and asserts 27 US-Letter pages, 6 figures, 5 tables, 22
references, no overfull boxes, and the prose style freeze. Standalone and
graphical-abstract exports are regenerated by hand when their own sources
change.
