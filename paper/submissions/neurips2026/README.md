# NeurIPS 2026 workshop skeletons

Two compile-ready starting points, condensed from `paper/crossaudit.tex`
(the 14-page position paper). The full plan, deadlines, and double-blind
checklist live in `../SUBMISSION-PLAN.md`.

| File | Target | Limit |
|---|---|---|
| `academia-long.tex` | AI-Native Academia @ NeurIPS 2026 (Atlanta) | 9 content pages |
| `molecular-5p.tex` | Agentic Systems for Molecular Sciences (Paris) | 5 content pages |

Build: `pdflatex <file>.tex` twice. Both compile today.

**Official style file:** download `neurips_2026.sty` from the workshop CFP
pages (or neurips.cc) and drop it in this directory — the skeletons switch to
it automatically via `\IfFileExists`; until then a dimension-compatible
fallback (letterpaper, 5.5in x 9in text block, Times) is used.

`shared/` holds assets extracted from the main paper: the Figure 1
tikzpicture, the Table 1 tabular (its `\cite` keys resolve once you paste the
bibliography), the full abstract, and the colour/macro preamble. Each
skeleton's comments carry the per-section page budgets and cut lists.
