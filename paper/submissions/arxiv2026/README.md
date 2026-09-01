# CrossAudit arXiv source

This directory is the upload-ready source layout for the next arXiv revision of
the CrossAudit paper. arXiv does not prescribe a visual paper template; the
manuscript therefore uses a conventional 11 pt, single-column, US Letter
`article` layout and only packages available in the standard TeX Live
distribution.

## Upload artifact

Upload an archive whose root contains exactly:

```text
main.tex
figures/figure5-v4-configuration-effects.pdf
figures/figure6-v4-operational-tradeoffs.pdf
```

The main document contains the complete bibliography and draws Figures 1--4
with TikZ. Figures 5--6 are vector PDF inputs. Do not add the locally compiled
`main.pdf`, `.aux`, `.log`, `.out`, temporary images, plotting code, or this
README to the arXiv source archive.

## Rebuild

From `source/`, run:

```sh
pdflatex -halt-on-error -interaction=nonstopmode main.tex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
```

Select PDFLaTeX during arXiv submission and inspect arXiv's generated PDF before
submitting. The source intentionally does not include a hand-written
`00README.json`: arXiv's current submission interface generates that compiler
record during upload.

The canonical editable manuscript remains `paper/crossaudit.tex`. Keep
`source/main.tex` byte-identical to it when preparing a replacement.
