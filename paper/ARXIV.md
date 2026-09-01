# arXiv submission — materials and checklist

Operator decision 2026-07-31: the paper goes to arXiv first; NeurIPS workshop
formatting (D2/D3/D4) is deferred and the scaffolds under `submissions/` stay
untouched until that lane reopens. The submitted artefact is the main paper,
authors visible (arXiv is not blind).

## Gate: the repositories must be public before this goes up

The paper says, in §4.5: *"We will publish them at a fixed release tag before
this paper is cited, and a reader who cannot reach them should discount every
statement below accordingly."* Posting to arXiv is the act that makes a paper
citable, so uploading while the repositories answer 403 breaks a promise the
paper makes in its own text.

Checked 2026-08-04: `crossaudit`, `crossaudit_v2` and `crossaudit_v3` all return
403 to an anonymous request. Eleven `\texttt{}` artefact citations and one pinned
commit (`5e5f2eade4`) point into them, and §4.4 now points at
`experiment/v3/SMOKE-FINDINGS.md` as well.

This is not a nicety. The paper's whole offer is that a third party can re-read
the ledger. A reader whose first action is a 403 has been handed a paper about
unverifiable supervision claims that is itself an unverifiable supervision
claim, and no amount of disclosure prose repairs that impression.

Before upload:

1. Make `crossaudit` public. `crossaudit_v2` and `crossaudit_v3` are cited only
   as the product line's evolution (§4.3); either make them public too or soften
   the citations to name them without implying they can be opened.
2. Cut a release tag and change §4.5's pinned `5e5f2eade4` to that tag if the
   default branch has moved past it.
3. Re-check anonymously (`curl -o /dev/null -w '%{http_code}'`), not from a
   logged-in browser, which will show you a page nobody else can see.

## Artefact bindings

The published v1 PDF has SHA-256
`2283e0d3b00d7095852b641266d602d38afcc0e74ad0cc2ea3c84346837841cc`
and is preserved at release tag `paper-v1.0.0`. The current replacement
candidate is a different 24-page artefact with six figures, four tables, and
twenty-two references. Its PDF SHA-256 is
`abf03342bdacf159b87cb31d134261c760bedb957fe68b969f4b874b85336afe`;
the TeX source SHA-256 is
`6f8767347eb665a998bc104fe2fd2a4e8dcc0bb0ba0f171582ddcf01b264e48b`.
The Figure 5 and Figure 6 input-PDF digests are respectively
`78bcc336947a1670f9fdaceeb5d96c0d0b9bafdcdfc6b05c6fc4ed9a4dd22d0d`
and
`c3bbb06461ae89c998f4d433a8bda25579f7b962042821d4450bb2c6dbe2d634`.
`paper/HASHES.txt` binds those build inputs and the quantitative-figure
provenance as one release set; regenerate it after any source, figure, or layout
change. Do not replace or move the historical tag when uploading v2.

## What gets uploaded

Upload one source bundle containing exactly these three build inputs, preserving
the relative paths:

```text
crossaudit.tex
figures/figure5-v4-configuration-effects.pdf
figures/figure6-v4-operational-tradeoffs.pdf
```

The bibliography remains an embedded `thebibliography`; Figures 1--4 remain
TikZ drawn in-document, while Figures 5--6 are Python-generated vector PDFs
included with `\includegraphics`. The current bundle was re-verified in a clean
temporary directory with two pdflatex passes and zero errors. The published v1
is 19 pages; the current v2 candidate is **24 pages as of 2026-09-01**, after
adding the sealed v4 feasibility results, Table~4, and Figures 5--6. Re-count
from arXiv's own generated PDF before submitting rather than trusting this line;
a paper about self-description that misdescribes itself in its own metadata is
an avoidable embarrassment.

No `.bbl`, PNG/SVG/TIFF previews, graphical-abstract exports, plotting scripts,
QA overlays, or other ancillary files are needed for compilation. The two PDFs
above are build inputs, not optional exports. If arXiv's current TeX processor
complains, inspect its build log for package-environment or path drift. All
packages used (geometry, amsmath, mathptmx, helvet, microtype, xcolor, graphicx,
tikz, booktabs, array, enumitem, placeins, hyperref, caption) are standard TeX
Live packages.

## Metadata for the submission form

- **Title:** CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic
  Science
- **Authors:** Zhaohe Dong (University of Cambridge), Yuhao Chen (University
  of Wisconsin–Madison)
- **Comments:** 24 pages, 6 figures, 4 tables, 22 references. Reference
  implementation, audit ledger, and experiment artefacts:
  https://github.com/dongzhaohe321418-lab/crossaudit
- **Primary category:** cs.AI. Suggested cross-lists: cs.SE (the mechanism is
  CI/git machinery), cs.CY (research integrity and accountability).
- **License:** arXiv non-exclusive license v1.0 is sufficient and keeps later
  venue options open; choose CC BY 4.0 only if you want to commit to it now.
- **Abstract field:** the paper's abstract is 1,581 plain characters after
  whitespace folding and the form caps at 1,920, so the paper's own abstract
  goes in verbatim. No
  condensation is needed and none should be invented: an abstract that differs
  between the listing and the PDF is a small dishonesty of exactly the kind
  this paper is about. Regenerate this block after any abstract edit.

```text
An AI scientist should not grade its own homework. Yet in the systems we
examined, review usually comes from the same model family or vendor as the work
it judges. Model evaluators are known to favour their own generations; shared
blind spots remain plausible but unproven. The supervision record often sits in
platform logs that outsiders cannot replay. We present CrossAudit, a protocol
for supervising autonomous research pipelines. Each increment is audited by an
agent from a different vendor against a versioned, human-authored rulebook.
Reports, verdicts, disputes and rulings are git commits; raw model exchanges are
not yet preserved. Scripted checks run first. Advisory judgement never gates: a
model blocks only by citing a rule, cannot waive a deterministic failure, and
unresolved blockers go to a person after bounded revision. We state eight
invariants, describe a GitHub Actions/Python reference implementation, and
report a live computational-chemistry deployment. We also report a
seeded-defect trial (30 increments, 43 defects, one run per configuration) whose
blinding a cross-vendor audit voided; we adopt the corrected results. A
separately sealed v4 execution-feasibility cohort completed 542 scheduled calls
and seven measurement modules on six deterministic convenience tasks. Its
mixed, configuration-specific results are non-confirmatory and support no
vendor-population claim. The trial shows that two vendors read the same
rulebook differently, not that either is better. The strongest evidence
remains the committed, uncontrolled audits of this paper.
```

## Operator checklist (the upload is yours)

1. arXiv account with an endorsed cs.AI submission path (institutional email
   usually suffices).
2. Upload the three-file source bundle listed above as the replacement source,
   keeping both PDFs under `figures/`; let arXiv build it and check that the
   generated PDF is 24 pages and Figures 1--6 and Tables 1--4 all render.
   (Count from arXiv's build itself, not from this line: this file has now twice
   carried a stale page count, which for this paper is not a forgivable class of
   error.)
3. Paste the metadata above; submit before the 14:00 ET weekday cutoff to get
   the next announcement cycle.
4. The identifier is assigned: `CITATION.cff` and both READMEs now cite
   `arXiv:2608.28631`. The repository About-field change remains an operator UI
   action if it has not already been made.
5. Any later revision to the TeX or either included figure that should reach
   arXiv is a replacement (v2, v3, …): upload the complete three-file build
   bundle again, and keep the mapping (commit ↔ arXiv version) honest in the
   ledger and commit message.

## What was deliberately not done

No de-anonymisation pass was needed (names are already in the paper); no
`\today` lurks (the date is fixed "September 2026"); the double-blind checklist in
`submissions/SUBMISSION-PLAN.md` §四 does not apply to arXiv and was not run.
