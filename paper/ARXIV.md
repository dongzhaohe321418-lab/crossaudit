# arXiv replacement submission

This checklist applies to the next replacement of arXiv:2608.28631. It does
not claim that the replacement has already been submitted. The public arXiv
version and its historical release tag must remain unchanged until the operator
uploads this candidate.

arXiv does not impose a journal-like visual template. The candidate uses a
portable, conventional preprint layout: `article`, 11 pt, single column, US
Letter, one-inch margins, fixed date, and standard TeX Live packages. It is not
in double-spaced referee mode.

## Public-artifact gate

Anonymous HTTP checks on 2026-09-02 returned:

```text
crossaudit     200
crossaudit_v2  200
crossaudit_v3  404
```

The paper links to `crossaudit_v3` in Section 4.3 and describes it as an MIT
licensed public implementation. Before upload, either make that repository
public at the cited location or revise the sentence so it does not claim a
retrievable public artefact. This content gate is independent of whether the
TeX source compiles.

## Canonical source and upload bundle

The editable manuscript is `paper/crossaudit.tex`. The arXiv upload layout is
under `paper/submissions/arxiv2026/source/`; its `main.tex` must remain
byte-identical to the canonical manuscript.

Upload an archive whose root contains exactly:

```text
main.tex
figures/figure5-v4-configuration-effects.pdf
figures/figure6-v4-operational-tradeoffs.pdf
```

The bibliography is an embedded `thebibliography`. Figures 1--4 are drawn with
TikZ; Figures 5--6 are vector PDFs included with `graphicx`. Do not upload the
compiled `main.pdf`, `.aux`, `.log`, `.out`, previews, plotting code, review
notes, or other unused files. arXiv compiles from the archive root.

Select PDFLaTeX. The source uses no shell escape, `minted`, hidden paths,
absolute paths, external documents, on-the-fly figure conversion, `\today`, or
`\pdfoutput` override. A hand-written `00README.json` is intentionally omitted;
the current arXiv interface creates the compiler record at upload time.

## Reproducible local build

From `paper/submissions/arxiv2026/source/`:

```sh
pdflatex -halt-on-error -interaction=nonstopmode main.tex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
```

The third pass is retained because the document has a dense float and
cross-reference graph. The verified local candidate has 27 US-Letter pages,
6 figures, 5 tables, and 22 references, with no undefined references or
overfull boxes. Re-count and visually inspect arXiv's generated PDF before the
final submit action.

## Submission metadata

- **Title:** When Does Independent Audit Help Agentic Science? CrossAudit and a
  Causal Evaluation Framework
- **Authors:** Zhaohe Dong (University of Cambridge); Yuhao Chen (University of
  Wisconsin--Madison)
- **Comments:** 27 pages, 6 figures, 5 tables, 22 references. Reference
  implementation, audit ledger, and experiment artefacts:
  https://github.com/dongzhaohe321418-lab/crossaudit
- **Primary category:** cs.AI
- **Suggested cross-lists:** cs.SE and cs.CY
- **License:** retain the license selected for arXiv:2608.28631 unless the
  authors deliberately choose a different license for the replacement.

The following ASCII-normalised abstract folds to 1,866 characters, below
arXiv's 1,920-character limit. Paste it into the form after verifying it still
matches the PDF:

```text
An AI scientist should not grade its own homework, but changing the grader does
not make the grade independent. Whether same-model, same-family, same-vendor,
and cross-vendor reviewers have meaningfully different error correlations
remains an empirical question; supervision records also often sit in platform
logs outsiders cannot inspect.

We present CrossAudit, a protocol and evaluation framework for supervising
autonomous research pipelines. Each increment is audited by an agent from a
different declared vendor against a versioned, human-authored rulebook. Reports,
verdicts, disputes and rulings are git commits; raw model exchanges are not yet
preserved. Scripted checks run first. A model blocks only by citing a rule,
cannot waive a deterministic failure, and unresolved blockers go to a person
after bounded revision. We formalise net correction under false-block,
revision-harm, model-cost, and human-attention constraints; vendor is an
assignment factor, not a synonym for independence.

We state eight invariants, describe a GitHub Actions/Python implementation, and
report a live computational-chemistry deployment. A sealed v4 feasibility cohort
completed 542 calls across seven modules and six deterministic convenience
tasks. It revealed direction heterogeneity, a Constitution-repeat estimand
mismatch, DCL/gold circularity, and no structured-ledger advantage over an
ordinary log on proxy decisions. These non-confirmatory engineering findings
are not evidence that cross-vendor review works. We therefore specify a
prospective v5 study with 150--180 tasks, three vendors, six pinned models,
same-model and
same-vendor/different-model controls, three domains, human-blinded gold, and
task-clustered inference. The present contribution is the protocol, executable
evaluation machinery, and falsifiable study design; efficacy remains
unestablished.
```

## Operator checklist

1. Resolve the `crossaudit_v3` public-artifact gate above.
2. Confirm `main.tex` is byte-identical to `paper/crossaudit.tex` and rebuild
   from a clean extracted archive.
3. Upload the three-file archive as a replacement for arXiv:2608.28631 and
   choose PDFLaTeX.
4. Inspect every page of arXiv's generated PDF. Confirm 27 pages, Figures 1--6,
   Tables 1--5, hyperlinks, affiliations, and the fixed `September 2026` date.
5. Paste the metadata above, compare the abstract to the PDF, then submit.
6. After announcement, update `CITATION.cff`, README links, and the release tag
   so the repository identifies the exact arXiv version and source hashes.
