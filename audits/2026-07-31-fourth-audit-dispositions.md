# Fourth audit (multi-skill, local clone) — dispositions

Three CRITICALs, all verified against experiment/ artefacts and ACCEPTED:
1. Scorer recall rises with finding volume (arms emitted 17/63/113 findings); permutation
   floors 4.7/22.4/31.9 of 43 — headline lenient comparison within noise, strict order
   reverses (κ .813 same-family vs .675 cross-vendor). Paper now reports both tiers + the
   permutation correction; the null-check script joins the ledger (score_nullcheck.py).
2. Strict-tier numbers existed in SCORECARD but were unreported and conclusion-flipping.
   Fixed: abstract, table, and §4.3 report lenient AND strict.
3. Cross-vendor arm's verdict was constant (BLOCKED 30/30) — disagreement, not
   discrimination; a block-everything stub reproduces its verdict accuracy. Disclosed
   verbatim; the unfalsifiable "vendor split is the result" framing withdrawn; §6
   economics made conditional (10/10 false-block ⇒ O(increments) escalations).
Citation nits fixed (szymanski2023 title; gottweis2025 retitle note). EIC suggestion
(recentre empirics on the self-audit chain, demote synthetic trial to feasibility)
adopted directionally in the abstract; full restructure queued for the major revision.
Reviewer verdict "Major Revision — evidence layer, rerun not rewrite": accepted.

APPENDED 2026-07-31 (sixth audit, R1): the floors in item 1 were computed by an
implementation that never entered the ledger, so the numbers above stood on an
unrecoverable artefact. `experiment/score_nullcheck.py` now exists and
regenerates them: 4.8/22.4/31.8 (2000 shuffles, seed 20260731), κ .813
same-family vs .677 cross-vendor. The figures above are superseded by those,
and are left unedited as the record of what was claimed at the time. See
`audits/2026-07-31-sixth-audit-dispositions.md`.
