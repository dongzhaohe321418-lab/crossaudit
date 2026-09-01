# Top-conference pre-results manuscript

`crossaudit-topconf.tex` is the compact main-track/Evaluation-and-Datasets
narrative derived from the full protocol paper.  It is intentionally labelled
as a pre-results draft because the human-adjudicated v5 confirmatory study has
not run.  The document has no TODO placeholders and can be rebuilt today, but
it is not submission-ready until the locked v5 results replace the prospective
results language.

The source uses a dimension-compatible fallback layout.  Replace it with the
official 2027 venue style once that style and call are published; do not infer
2027 requirements from the 2026 template.

Build from this directory:

```bash
pdflatex -interaction=nonstopmode -halt-on-error crossaudit-topconf.tex
pdflatex -interaction=nonstopmode -halt-on-error crossaudit-topconf.tex
```
