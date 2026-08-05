# Dispositions: external Major-Revision review of 2026-08-05

The reviewer checked out the pinned commit, re-ran the scoring scripts,
reproduced the chance floors, ran the 65 controller tests, and verified the key
hash before writing a word. This repository owes that standard of review its
own standard of response: every claim verified before action, every acceptance
implemented or scheduled, every declination argued.

## Verification of the review's own claims

| Review claim | Checked | Result |
|---|---|---|
| Duplicate sentence, p. 17 ("the receipt can record … and The receipt can record") | grep | **Confirmed**, fixed |
| Empty Acknowledgements heading | grep | **Confirmed**, removed |
| Refs [1]/[3] "C. Lu, C. Lu" ambiguous | bibliography read | **Confirmed**, expanded to Chris Lu / Cong Lu / Robert Tjarko Lange |
| Chen et al. 2025 (arXiv:2504.03846) exists and qualifies self-preference | fetched abstract | **Confirmed**; cited |
| Roytburg et al. 2026 (arXiv:2601.22548) exists; ~51% of cases survive identity-blind re-test | fetched abstract | **Confirmed**; cited |
| Ref [4] has a 2026 Nature version with DOI | web search | **Not confirmed.** The only Nature-family hit is a Nature Medicine commentary ("The AI co-scientist is here"), not the paper. Entry stays as arXiv with the retitle note; revisit when a journal record is verifiable |
| Committed NULLCHECK.json records `p_value: 0.0` | read artefact | **Confirmed**; script now uses (b+1)/(N+1), artefact regenerated (floors unchanged, p now 0.0005) |
| Paper PDF ≠ pinned commit ≠ remote main | partially checkable | **Accepted on the reviewer's evidence.** This working clone has no configured git remote, so remote state is not observable from here; the structural fix (tag anchor, artefact binding) does not depend on the unobservable part |
| crossaudit public, crossaudit_v3 private as of 2026-08-05 | curl | **Not checkable from this environment** (github.com returns 403 to all four repositories here, including ones the reviewer demonstrably read, so the 403 measures this sandbox's egress, not visibility). §4.5 rewritten to the per-repo statement the reviewer reports; operator must confirm from an incognito browser |
| Product line now at V4 4.14.0 | not checkable here | Footnote hardened instead: evidence frozen at v3 3.2.0, later product versions declared outside this paper's evidence |

## Major findings

**1. The trial has no generator vendor, so it cannot test cross-vendor
supervision.** Accepted in full. This is the review's best finding. Fixed by
(a) stating in the design paragraph that no model authored the corpus, the arm
labels name auditor configurations only, and the own-generation setting of
self-preference is not instantiated; (b) renaming "same-family/cross-vendor
arm" to Claude-family/GPT-family configuration labels throughout §4.4;
(c) replacing "Vendor heterogeneity produced observably decorrelated readings"
with a configurations-not-pairings statement stripped of the causal verb.
The genuinely crossed design the reviewer asks for is already the registered
v3 study (per-vendor authored corpora; registration and AMENDMENT 1), which is
blocked on operator credentials, not on design work.

**2. The paper outran its pinned commit.** Accepted. §4.5 now anchors to
release tag `paper-v1.0.0`, names the failure ("caught by the external review
of this paper having moved past its own pin"), and the repository's tracked
PDF is byte-identical to the submitted one, SHA-256 recorded in ARXIV.md.
The tag itself must be created by the operator at the final commit; ARXIV.md
gates the upload on it.

**3. Self-preference literature over-extended.** Accepted. Both qualifying
papers verified and cited; §2 now says the foreclosed configuration is
narrower than the headline effect and is a structural precaution, not a
quantified harm averted. I1's rationale already carried "an effect this paper
does not measure"; it stands.

**4. Invariant vs implementation conflated.** Accepted. "An implementation is
CrossAudit when it preserves the following" is now a conformance-degree
statement; "invariant" is reserved for the protocol's obligation. The named
conformance-profile ladder (core / receipted / gated / recorded / replayable /
attested) is good revision-2 specification work and is recorded in
ROADMAP-R2.md rather than promised in the paper.

**5. I3/I8 precedence contradiction.** Accepted with one correction of fact:
the admission path already fails closed on `audit_integrity != OK`, with a
test (`controller/tests/test_receipt_admission.py::
test_failed_audit_integrity_is_not_admissible`), so the combined case cannot
admit today. What was wrong was the paper: I3 now states verdict precedence
normatively; the status paragraph separates what is enforced (validation,
admission refusal) from what revision 2 owes (relabelling the recorded verdict
itself); Table 2's I3 row no longer reads plain "Enforced".

**6. Git-ledger guarantees overstated.** Accepted. Abstract no longer claims
every artefact is a commit or that raw exchanges are preserved; "certifies"
became "records"; the Table 1 ledger column dropped the word "public";
the §4.5 availability statement is per-repository. The threat model's
operator-rewrite admission already existed and now nothing upstream
contradicts it.

**7. Deployment statistics under-specified.** Accepted. The 21-cycle passage
now states units for every number: 39 finding occurrences vs 23 distinct
identifiers vs 20 closed; closure lag defined per distinct finding over the 20
closed with the 3 open excluded, not imputed; the 33/12 scope counts labelled
as overlapping finding–scope incidences; the 6-minute and 34-minute medians
given with their actual definitions (audit duration vs audit-to-next-audit
interval) and spreads; second-freeze hashes in the text and the two freezes
distinguished in Figure 4's caption.

**8. "Within noise" had no statistic.** Accepted. `experiment/arm_contrast.py`
(labelled post hoc, seeded, self-validating against the published totals)
computes the direct paired test: lenient tier +3 of 43, discordant 5 vs 2,
exact McNemar p=0.45, bootstrap 95% CI [−2, +8]; strict tier −1, p=1.0,
CI [−7, +5]. The paper now reports exactly this and states that the floors do
not test the between-arm gap. "Verdicts (of 30)" renamed "Verdict accuracy".
The 26 clean-increment blockers still lack per-finding adjudication; that
remains operator work and the paper still says so.

**9. Table 1 compared a specification against implementations.** Accepted.
CrossAudit appears twice (protocol row, reference-implementation row with ~ on
the ledger column); caption states the set is chosen, not surveyed, and names
the two rows' different objects.

**10. Too many papers in one paper.** Declined for this arXiv version,
recorded for the venue version. The restructure (product material to an
appendix or companion report) is real work the operator should scope; Table 3
already binds each object to its claims and evidence, which is the
load-bearing part of the reviewer's request. Declining a structural rewrite
hours before a preprint upload is a schedule judgement, not a disagreement.

## Minor findings

Duplicate sentence fixed; empty Acknowledgements removed; Lu names expanded;
ref [4] unverifiable (above); footnote-size and Figure-2 whitespace deferred as
cosmetic; report-before-receipt ordering added to the loop figure's caption;
"misevaluated" → "miscalculated"; the cents estimate replaced by the size
asymmetry with an explicit refusal to quote an unmeasured price; per-repo
visibility statement; v3 version freeze hardened; tagged-PDF accessibility
deferred (tagpdf with a heavy TikZ document is not a pre-upload change) and
noted for the venue version.

## What this review changes about the paper's claim

Nothing in the protocol, and one word in the thesis. The paper now says,
explicitly and in more places, what the strongest honest version of it always
was: a protocol and engineering design that makes heterogeneous-model
supervision inspectable and fail-closed, under which whether cross-vendor
assignment improves audit accuracy is a registered, still-open empirical
question. The reviewer's suggested repositioning sentence and the paper's
existing §4.4 hedges now agree with each other everywhere, including the
abstract.
