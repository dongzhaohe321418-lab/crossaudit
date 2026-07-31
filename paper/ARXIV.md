# arXiv submission — materials and checklist

Operator decision 2026-07-31: the paper goes to arXiv first; NeurIPS workshop
formatting (D2/D3/D4) is deferred and the scaffolds under `submissions/` stay
untouched until that lane reopens. The submitted artefact is the main paper,
authors visible (arXiv is not blind).

## What gets uploaded

`crossaudit.tex` alone. The paper is fully self-contained: bibliography is an
embedded `thebibliography`, every figure is TikZ drawn in-document, there are
no `\input`/`\includegraphics` and no external assets. Verified 2026-07-31 by
compiling the single file in an empty directory: two pdflatex passes, zero
errors, 15 pages (TeX Live 2025; arXiv runs TeX Live, pdflatex path).

No `.bbl`, no figures directory, no ancillary files needed. If arXiv's
AutoTeX complains about anything, it will be package-environment drift; all
packages used (mathptmx, helvet, microtype, xcolor, tikz, booktabs, array,
enumitem, hyperref, caption) are standard TeX Live.

## Metadata for the submission form

- **Title:** CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic
  Science
- **Authors:** Zhaohe Dong (University of Cambridge), Yuhao Chen (University
  of Wisconsin–Madison)
- **Comments:** 15 pages, 3 figures, 2 tables. Reference implementation,
  audit ledger, and experiment artefacts:
  https://github.com/dongzhaohe321418-lab/crossaudit
- **Primary category:** cs.AI. Suggested cross-lists: cs.SE (the mechanism is
  CI/git machinery), cs.CY (research integrity and accountability).
- **License:** arXiv non-exclusive license v1.0 is sufficient and keeps later
  venue options open; choose CC BY 4.0 only if you want to commit to it now.
- **Abstract field:** the paper's abstract is 2,781 plain characters and the
  form caps at 1,920, so the field takes the condensed version below
  (1,894 chars). The in-paper abstract is untouched; the condensation drops
  the blinding-voided parenthetical and the strongest-evidence sentence,
  which the paper itself states in full.

```text
Autonomous "AI scientist" systems increasingly generate, execute, and review
research. In the frontier systems we survey, the reviewing agent is an
internal critic chosen by the same operator, often from the same model family
or vendor as the generating agent, exposing supervision to self-preference
bias and to shared blind spots; the supervision trace usually lives in opaque
platform logs rather than in an artefact a third party can replay. We present
CrossAudit, a lightweight protocol for supervising autonomous research
pipelines, built on three commitments: heterogeneity (every experiment
increment produced by a generator agent is audited by an agent from a
different model vendor, against a versioned, human-authored rulebook); a
git-native ledger (experiments, audit reports, verdicts, disputes and
escalations are all commits, so the supervision history can be re-read,
diffed, and cited); and graded human oversight (deterministic checks gate the
pipeline, judgement calls do not, and a bounded revision loop escalates
unresolved blockers to a human principal). We specify the protocol as eight
invariants; describe a public reference implementation that targets them and
implements a subset; and report a live deployment in a computational-chemistry
pipeline. In an exploratory seeded-defect trial (30 synthetic increments, 43
defects), a same-family auditor scored 38/43 with zero false-positive
blockers, while a cross-vendor auditor scored 41/43 at a lenient scoring tier
but 37/43 at a strict tier and blocked all thirty increments;
permutation-corrected agreement places the two model arms within noise at the
lenient tier and reverses their order at the strict tier. The trial shows
that vendors disagree, not that either is better. We argue that cross-vendor
audit trails are a practical basis for accountable machine science, and one a
single researcher can adopt today.
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
