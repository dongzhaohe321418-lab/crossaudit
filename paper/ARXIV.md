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

## Final artefact binding (2026-08-05)

The PDF this metadata describes has SHA-256 `ac44286f5b01935f537a460e7dcf4c5b3953e7ca10b6f625dee85b68a7b44889`.
`paper/crossaudit-paper.pdf` in the repository is that same file, byte for byte.
The paper's §4.5 now cites release tag `paper-v1.0.0` instead of a bare
commit; **create that tag at the final commit and push it before uploading**,
because the external review caught the previous draft having moved past its own
pinned commit, and the fix only holds if the tag actually exists.

## What gets uploaded

`crossaudit.tex` alone. The paper is fully self-contained: bibliography is an
embedded `thebibliography`, every figure is TikZ drawn in-document, there are
no `\input`/`\includegraphics` and no external assets. Re-verified 2026-08-03 by
compiling the single file in an empty directory: two pdflatex passes, zero
errors (TeX Live 2025; arXiv runs TeX Live, pdflatex path). **19 pages as of
2026-08-04** -- 15 at the first check, 17 at the second, 19 now. Re-count before
submitting rather than trusting this line; a paper about self-description that
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
- **Comments:** 19 pages, 4 figures, 3 tables, 22 references. Reference
  implementation, audit ledger, and experiment artefacts:
  https://github.com/dongzhaohe321418-lab/crossaudit
- **Primary category:** cs.AI. Suggested cross-lists: cs.SE (the mechanism is
  CI/git machinery), cs.CY (research integrity and accountability).
- **License:** arXiv non-exclusive license v1.0 is sufficient and keeps later
  venue options open; choose CC BY 4.0 only if you want to commit to it now.
- **Abstract field:** the paper's abstract is 1,770 plain characters and the
  form caps at 1,920, so the paper's own abstract goes in verbatim. No
  condensation is needed and none should be invented: an abstract that differs
  between the listing and the PDF is a small dishonesty of exactly the kind
  this paper is about. Regenerate this block after any abstract edit.

```text
An AI scientist should not grade its own homework. Yet in the systems we
examined, the agent that reviews the work usually comes from the same model
family as the agent that produced it, or at least from the same vendor. Model
evaluators are known to favour their own generations. Whether models trained
alike also share blind spots is a conjecture, not a settled finding, but if
they do, the reviewer inherits the author’s. The record of what was flagged
and what was waved through often sits in platform logs that nobody outside can
replay. We present CrossAudit, a protocol for supervising autonomous research
pipelines. It rests on three commitments. Each increment of work is audited by
an agent from a different vendor, against a rulebook a human wrote and
versioned. Reports, verdicts, disputes and rulings are git commits, so the
supervision history can be re-read and cited; raw model exchanges are not yet
part of that record. Scripted checks run before any model does. Advisory
judgement never gates the pipeline: a model blocks only by citing a rule, and
no model may waive a deterministic failure. Blockers that survive a bounded
number of revision rounds go to a person. We state the protocol as eight
invariants. We describe a reference implementation built from GitHub Actions
and a few hundred lines of Python, and report a live deployment in a
computational-chemistry pipeline. We also ran a seeded-defect trial. A cross-
vendor audit of our own repository then voided its blinding. We adopt that
audit’s findings and report the corrected results. The trial shows that two
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
