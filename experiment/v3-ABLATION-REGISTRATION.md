# v3 registration — ablation study: who finds the errors, and through which channel

Registered 2026-07-31, prior to any new model arm being run. Extends (does not
replace) `experiment/v2-REGISTRATION.md`. The operator proposed the two study
questions; this document freezes how they will be answered.

**Q1.** Does an independent audit agent find more (and more real) defects than
the executing agent reviewing its own work?
**Q2.** How much do the three supervision channels each contribute: the
natural-language Constitution (LLM-applied), executable generic rules (DCL),
and scientific-tool verification?

## Part A — synthetic corpus (recall instrument)

Known seeded defects give exact recall denominators; everything below runs on
one shared corpus so comparisons are per-defect paired.

| Arm | Configuration | Isolates |
|---|---|---|
| A0 | constant-BLOCK stub | finding-volume null |
| A1 | generic DCL scripts (schema, units, provenance, convergence) | executable-rule channel |
| A2 | domain tools (parser round-trip, SCF monotonicity, cell/symmetry self-consistency, physical bond lengths) | scientific-tool channel |
| A3 | same-vendor LLM, **generation transcript attached** | in-context self-review proxy |
| A4 | same-vendor LLM, fresh context, **no Constitution** | model prior alone |
| A5 | same-vendor LLM, fresh context, with Constitution | baseline |
| A6 | cross-vendor LLM, fresh context, with Constitution | parametric isolation |

Primary contrasts (Holm-corrected; McNemar exact on per-defect pairs):
C1 A3 vs A5 (contextual isolation), C2 A5 vs A6 (cross-vendor), C3 A4 vs A5
(Constitution contribution), C4 marginal catches of A1/A2 over the A5+A6 union
(channel decomposition). Precision is co-primary: blocker rate on clean
increments per arm. Corpus target ~60 increments / ~100 defects, each defect
pre-tagged with its cheapest catching channel; corpora authored per vendor
(v2 rule); defect key sealed with a third party BEFORE generation (v2 rule;
the v1 seal failure is documented in the paper).

Transcripts for A3 are model-generated rationalisations of each increment,
written blind to the defect key; they may rationalise defective values but
never name a defect. Both directions of Q1 are informative: transcript access
helping (information) or hurting (anchoring, self-preference).

## Part B — the real deployment ledger (precision + ecological validity)

Source: the operator's live pipeline. Data freeze (read-only clones):
`perovskite-screening` @ `af0dc58713b9bcf675fb324a262024f39127f8a7`,
`perovskite-screening-audit` @ `88b92429ee3ccc7650c98baef0d973abfc0e131d`.
Mined by `v3/mine_ledger.py` (its committed version is part of this freeze);
committed artifacts are Level-B redacted (structure verbatim, free text
hashed), per `ledger-mirror/REDACTION.md`.

What the ledger already contains (computed key-less, 2026-07-31):
7 audited cycles over 2 days; decisions BLOCK, BLOCK, BLOCK, BLOCK, BLOCK,
PASS_WITH_CAVEATS, PASS; findings per cycle 7, 4, 3, 2, 1, 1, 0; 14 distinct
findings, of which **12 behaviourally confirmed real** and 2 unresolved at
freeze; auditor models gpt-5 / gpt-5.6 / gpt-5.6-sol via codex-cli; 7
science-side fix commits, each naming the finding IDs it closes. The audit
ledger holds no CYCLE-000003 artifact; the science history records a
"CYCLE-000003 Tier-0 follow-up" commit (deterministic-tier leg without a
model audit) — reported as-is.

**Frozen label rule.** CONFIRMED_REAL = the finding ID appears in a later
cycle's `verified_closed_findings`, or a science-repo commit subject names it
as fixed. UNRESOLVED = still open at freeze; excluded from precision metrics.
No other label source is admissible retroactively.

**Re-audit arms** (same seven pinned commits, fresh contexts): B4 same-vendor
without Constitution; B5 same-vendor with the deployment's own audit
instructions; B6 cross-vendor replication (test-retest against the historical
reports, which themselves constitute the natural B6 arm). A same-vendor
in-context arm is impossible: the generator's session state was never
committed — recorded as evidence for invariant I2, not worked around.

**Endpoints.** (i) Precision proxy per arm: fraction of findings matching a
CONFIRMED_REAL item (matching = same finding ID where cited, else overlap of
evidence file paths; rule frozen now). (ii) New-finding adjudication: the
human principal judges the pooled novel findings blinded to arm, order
shuffled, before arm identities are revealed; the harness performs no
scientific judgment. (iii) Mechanisability fraction: share of CONFIRMED_REAL
findings a script could have caught (draft classification by the harness from
structural fields, confirmed finding-by-finding by the principal) — this
number is the measured size of "the DCL you should have written" and feeds
the standards-ratchet argument. (iv) Convergence economics: the decay curve,
closure lag in cycles, severity mix — the deployment's own livelock evidence.

Given n=14 findings and 7 cycles, Part B is reported as a labelled case
series with exact (Clopper-Pearson) intervals; no arm-ranking claims will be
made from Part B alone. Part A carries the recall comparisons; Part B carries
precision and ecology. 

## Blockers and compliance

Model arms await fresh API keys for both vendors (all previously used keys
are burned and must be revoked); key custody per v2's escrow rule. The
science repositories are read-only inputs: nothing in them is modified, and
no scientific content is quoted in committed artifacts beyond hashed digests.
Amendments to this design land only as dated AMENDMENT sections below; the
scoring code referenced here may not change after the first model arm runs.

## AMENDMENT 1 (2026-07-31, operator-proposed) — the isolation ladder

Part A's arms are reorganised as a monotone ladder; each rung adds exactly one
layer of isolation between producer and reviewer. Channel arms (A0 stub, A1
DCL, A2 domain tools) are unchanged and orthogonal.

| Rung | Reviewer configuration | Adds |
|---|---|---|
| L0 | **no audit** -- increments admitted as produced | nothing (floor) |
| L1 | **self-reflection, same session**: the generating session is asked to review its own increment | a review step |
| L2 | same model, fresh instance, generation transcript attached | a context boundary |
| L3 | same model, fresh instance, no Constitution | transcript removed |
| L4 | same model, fresh instance, with Constitution | decidable rules |
| L4b | same vendor, **different model**, with Constitution | model separation |
| L5 | different vendor, with Constitution | vendor separation |

L0 contributes two anchors: recall floor (0 catches) and false-block floor
(0), and in cost accounting the number of defective increments that would
have been admitted unsupervised. L4 is what "same model, different prompt as
auditor" denotes; L4b sharpens it to same-vendor/different-weights.

**Pre-registered confound, L1/L2.** Corpus defects are injected by a
deterministic mutator into increments the generator itself authored, so the
in-session reviewer retains memory of the pre-mutation content. This biases
L1 (and, weaker, L2) TOWARD detection. Interpretation is therefore one-sided:
if self-review still underperforms the fresh-context rungs despite the memory
advantage, the deficit is robust; if it outperforms, no claim is made beyond
"memory advantage dominates". Recorded here before any arm runs.

**Analysis update.** Primary: trend across L1..L5 (Cochran's Q on the paired
per-defect catch matrix, plus adjacent-rung exact McNemar, Holm over the four
adjacent pairs). Co-primary unchanged (clean-increment false-block rate per
rung, same ladder). Channel decomposition contrasts unchanged. Cost endpoint
added: catches per false block and per dollar per rung, with L0 as
denominator anchor.

**Part B mapping.** L0 realises as the counterfactual already in the mined
ledger: absent the loop, the 12 behaviourally confirmed defects ship
downstream unchallenged. L1/L2 remain impossible on real data (generator
sessions were never committed; evidence for I2). L4 = B5, L4b runs if the
same-vendor second model is available under the escrowed keys, L5 = B6 and
the historical reports themselves.

## AMENDMENT 2 (2026-07-31, operator-proposed) — Part C: auditing code, not just data

Rationale. Data defects corrupt one increment; a defective analysis script
corrupts every increment it touches. Code is also where the deterministic
layer is weakest and reviewer judgment matters most — precisely the regime
where same-source bias is most dangerous, since vendors share training
exposure to the same public code corpus and its idiomatic bugs.

**Corpus (mutation-testing methodology).** Correct, tested analysis scripts
in the reference-increment style (unit conversion, convergence extraction,
tabulation) are mutated by a deterministic mutator: dropped unit conversions,
inverted convergence predicates, off-by-one column selections, silenced
exceptions, boundary-condition flips. Ground truth = the mutation log, sealed
under the same third-party rule as Part A. Each mutant is pre-tagged with its
cheapest catching channel, which for code has a finer gradation:

| Channel | Instrument | Example mutant class |
|---|---|---|
| syntactic | linter | unused/shadowed variable |
| type-level | type checker | unit-carrying type dropped |
| test-killable | existing test suite | inverted predicate a test exercises |
| tool-verifiable | dry-run on toy fixture + output-contract check | schema drift in emitted results |
| review-only | none of the above kills it | semantically wrong but type-safe, test-surviving |

The **review-only stratum is the measurement target**: the fraction of
seeded semantic bugs that survive every deterministic instrument but are
caught by model review, per rung of the isolation ladder (L1–L5 reused
verbatim), is the quantified value of cross-vendor code audit — the
operator's "ambiguity" made a number. Equivalent-mutant risk is handled by
pre-run adjudication: before any arm runs, each mutant is confirmed
behaviour-changing on the toy fixture; mutants that are not are discarded
and logged.

**Deterministic layer for code (new DCL members, also deployable to the
reference implementation):** lint, type check, test-suite execution,
dry-run-on-fixture with output-contract comparison, and diff-coverage
(changed lines must be executed by at least one test). Constitution gains a
draft `CA-CODE-*` rule family (see `templates/AUDIT_RULES_CODE.md`);
promotion of any CA-CODE rule from ADVISORY to BLOCKER follows the
shadow-mode ratchet, not this experiment.

**Endpoints.** Same ladder trend + channel decomposition as Part A, computed
separately for code; co-primary false-positive rate on unmutated scripts;
cross-part comparison (are isolation effects larger for code than for data
increments? — the operator's hypothesis, pre-registered here as directional).
Part B tie-in: the deployment's own scripts at the frozen SHAs may be
re-audited under B4–B6, with findings adjudicated by the principal; no
mutation ground truth exists there, so real-code results report precision
only.
