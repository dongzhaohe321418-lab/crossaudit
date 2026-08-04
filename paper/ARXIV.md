# arXiv submission — materials and checklist

Operator decision 2026-07-31: the paper goes to arXiv first; NeurIPS workshop
formatting (D2/D3/D4) is deferred and the scaffolds under `submissions/` stay
untouched until that lane reopens. The submitted artefact is the main paper,
authors visible (arXiv is not blind).

## What gets uploaded

`crossaudit.tex` alone. The paper is fully self-contained: bibliography is an
embedded `thebibliography`, every figure is TikZ drawn in-document, there are
no `\input`/`\includegraphics` and no external assets. Re-verified 2026-08-03 by
compiling the single file in an empty directory: two pdflatex passes, zero
errors, 17 pages (TeX Live 2025; arXiv runs TeX Live, pdflatex path).

No `.bbl`, no figures directory, no ancillary files needed. If arXiv's
AutoTeX complains about anything, it will be package-environment drift; all
packages used (mathptmx, helvet, microtype, xcolor, tikz, booktabs, array,
enumitem, hyperref, caption) are standard TeX Live.

## Metadata for the submission form

- **Title:** CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic
  Science
- **Authors:** Zhaohe Dong (University of Cambridge), Yuhao Chen (University
  of Wisconsin–Madison)
- **Comments:** 17 pages, 3 figures, 2 tables. Reference implementation,
  audit ledger, and experiment artefacts:
  https://github.com/dongzhaohe321418-lab/crossaudit
- **Primary category:** cs.AI. Suggested cross-lists: cs.SE (the mechanism is
  CI/git machinery), cs.CY (research integrity and accountability).
- **License:** arXiv non-exclusive license v1.0 is sufficient and keeps later
  venue options open; choose CC BY 4.0 only if you want to commit to it now.
- **Abstract field:** the paper's abstract is 1,627 plain characters and the
  form caps at 1,920, so the paper's own abstract goes in verbatim. No
  condensation is needed and none should be invented: an abstract that differs
  between the listing and the PDF is a small dishonesty of exactly the kind
  this paper is about. Regenerate this block after any abstract edit.

```text
An AI scientist should not grade its own homework. Yet in the systems we
surveyed, the agent that reviews the work usually comes from the same model
family as the agent that produced it, or at least from the same vendor. Model
evaluators are known to favour their own generations. Whether models trained
alike also share blind spots is a conjecture rather than a settled finding,
but if they do, the reviewer inherits the author's. The record of what was
flagged and what was waved through often sits in platform logs that nobody
outside can replay. We present CrossAudit, a protocol for supervising
autonomous research pipelines. It rests on three commitments. Each increment
of work is audited by an agent from a different vendor, against a rulebook a
human wrote and versioned. Every artefact of that supervision is a git commit,
so the history can be re-read and cited by anyone. Scripted checks run before
any model does. Judgement calls never gate the pipeline. Blockers that survive
a bounded number of revision rounds go to a person. We state the protocol as
eight invariants. We describe a reference implementation built from GitHub
Actions and a few hundred lines of Python, and report a live deployment in a
computational-chemistry pipeline. We also ran a seeded-defect trial. A cross-
vendor audit of our own repository then voided its blinding. We adopt that
audit's findings and report the corrected results. The trial shows that two
vendors read the same rulebook differently. It does not show that either is
better. The strongest evidence here is the committed record of cross-vendor
audits of this paper itself.
```

## Operator checklist (the upload is yours)

1. arXiv account with an endorsed cs.AI submission path (institutional email
   usually suffices).
2. Upload `paper/crossaudit.tex` as the source; let AutoTeX build; check the
   generated PDF is 15 pages and Figures 1–3 and Tables 1–2 render.
3. Paste the metadata above; submit before the 14:00 ET weekday cutoff to get
   the next announcement cycle.
4. After the identifier is assigned: update `CITATION.cff` (the `url` gains a
   preferred-citation with the arXiv id; the "arXiv 链接将更新于此" line in
   both READMEs resolves), and add the id to the repository About field.
5. Any later revision to `crossaudit.tex` that should reach arXiv is a
   replacement (v2, v3, …): same single-file upload, and the ledger keeps the
   mapping (commit ↔ arXiv version) honest in the commit message.

## What was deliberately not done

No de-anonymisation pass was needed (names are already in the paper); no
`\today` lurks (the date is fixed "July 2026"); the double-blind checklist in
`submissions/SUBMISSION-PLAN.md` §四 does not apply to arXiv and was not run.
