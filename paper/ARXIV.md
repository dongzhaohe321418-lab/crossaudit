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
candidate is a different 22-page artefact: `paper/crossaudit-paper.pdf` has
SHA-256 `8bf61ef2d248d2b35f7df6fe563093c2e89a5b027bb10a39bcac0973160016d1`
and its source has SHA-256
`a9c945aae48189b7bd4099b09949af9ceb0359a590a59aefab31f1fa121ca2ce`.
`paper/HASHES.txt` binds those current candidate bytes. Do not replace or move
the historical tag when uploading v2.

## What gets uploaded

`crossaudit.tex` alone. The paper is fully self-contained: bibliography is an
embedded `thebibliography`, every figure is TikZ drawn in-document, there are
no `\input`/`\includegraphics` and no external assets. Re-verified 2026-08-03 by
compiling the single file in an empty directory: two pdflatex passes, zero
errors (TeX Live 2025; arXiv runs TeX Live, pdflatex path). The published v1 is
19 pages; the current v2 candidate is **22 pages as of 2026-09-01**, after
adding the sealed v4 feasibility results and Table~4. Re-count before submitting
rather than trusting this line; a paper about self-description that
misdescribes itself in its own metadata is an avoidable embarrassment.

No `.bbl`, no figures directory, no ancillary files needed. If arXiv's
AutoTeX complains about anything, it will be package-environment drift; all
packages used (mathptmx, helvet, microtype, xcolor, tikz, booktabs, array,
enumitem, hyperref, caption) are standard TeX Live.

## Metadata for the submission form

- **Title:** CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic
  Science
- **Authors:** Zhaohe Dong (University of Cambridge), Yuhao Chen (University
  of Wisconsin–Madison)
- **Comments:** 22 pages, 4 figures, 4 tables, 22 references. Reference
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
2. Upload `paper/crossaudit.tex` as the replacement source; let AutoTeX build;
   check the generated PDF is 22 pages and Figures 1–4 and Tables 1–4 render.
   (Count from the AutoTeX build itself, not from this line: this file has now
   twice carried a stale page count, which for this paper is not a forgivable
   class of error.)
3. Paste the metadata above; submit before the 14:00 ET weekday cutoff to get
   the next announcement cycle.
4. The identifier is assigned: `CITATION.cff` and both READMEs now cite
   `arXiv:2608.28631`. The repository About-field change remains an operator UI
   action if it has not already been made.
5. Any later revision to `crossaudit.tex` that should reach arXiv is a
   replacement (v2, v3, …): same single-file upload, and the ledger keeps the
   mapping (commit ↔ arXiv version) honest in the commit message.

## What was deliberately not done

No de-anonymisation pass was needed (names are already in the paper); no
`\today` lurks (the date is fixed "September 2026"); the double-blind checklist in
`submissions/SUBMISSION-PLAN.md` §四 does not apply to arXiv and was not run.
