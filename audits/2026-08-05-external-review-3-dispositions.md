# Dispositions: third external review of 2026-08-05 (Major Revision, 5.5/10)

This reviewer ran the code: 65 tests reproduced, `score.py`,
`score_nullcheck.py` and `arm_contrast.py` outputs confirmed against the
paper's numbers, and the public tag's artefacts hashed and compared against
the PDF under review. Two of its six major findings are resolved with code
rather than prose, which is the resolution both of the day's earlier reviews
also pointed at.

## Finding 1 — the tag does not contain the reviewed PDF. Right, and diagnosed.

The reviewer found tag `paper-v1.0.0` (their commit `c9fdc906`) carrying the
`349c4eb9…` PDF with `\date{July 2026}`, while the version of record is
`d0a0faaa…` (August). Root cause is synchronisation lag, not a phantom
version: the tag was cut from the state of sync bundle *c* (the twenty-two
fix), before bundle *d* (the ninth audit, which contains the July→August
correction among 27 fixes) had been applied and the tag moved. The standing
instruction to apply *d* and recut was already in flight; it is superseded by
bundle *e*, which contains this commit.

Accepted beyond the sync fix: the phrase "the commit that builds this exact
PDF" promised byte-level rebuild determinism TeX does not offer. §4.5 now
anchors "exact" to the committed artefact and its digest, and
`paper/HASHES.txt` is the manifest a release must ship with. The operator's
recut checklist gains one line: verify the tag's `crossaudit-paper.pdf`
hashes to the manifest before announcing anything.

## Finding 2 — I3 unsatisfied and the text self-contradictory. Right; fixed in code.

The verdict synthesis in `run_llm_audit.py` ordered DCL-block above
invalid-reply, so the combined case recorded `BLOCKED` and absorbed the
integrity failure — exactly what I3 forbids and what §5's "convert to
escalation" already promised. The synthesis is now a pure function with I3
above I4 (`synthesise_verdict`), and
`controller/tests/test_verdict_precedence.py` pins seven cases, including
the two that matter: DCL-fail + invalid reply → `ESCALATE`, and valid model
`PASS` + DCL-fail → `BLOCKED`, so the reordering waives nothing. Suite:
65 → 72 passing. §4.1 and Table 2 now describe the implemented behaviour;
the §5 sentence stands because it is now true. The escalation object the
reviewer asks for is the existing escalation-issue route, which the relabelled
verdict now reaches.

## Finding 3 — wrong independence unit in the arm statistics. Right; recomputed.

The 43 defects nest inside 20 defective increments and every reply is
increment-level. `arm_contrast.py` now computes a cluster bootstrap and a
cluster sign-flip permutation over increments as the primary inference,
retaining the defect-level numbers as labelled-secondary: lenient +3 of 43,
cluster CI [−2, +8], cluster p = 0.46; strict −1, cluster CI [−6, +4],
p = 1.0. The reviewer's own cluster bootstrap predicted the conclusion would
not flip, and it does not; the method now matches the data structure, which
is the point. §4.4 states the nesting and cites the cluster figures;
"observably decorrelated" became "discordant" (no correlation was computed).
Per-model repeated calls remain future work under the registered study.

## Finding 4 — I1 marks overstate a self-declared string. Right.

Table 1's implementation row now shows ∼ for the cross-vendor critic column;
the caption already carried the reason. The three-way invariant split
(declared isolation / credential isolation / attested identity) is recorded
as revision-2 specification work alongside the conformance profiles.

## Finding 5 — ledger completeness overstated in two sentences. Right.

"Every input and output lives on GitHub" → committed artefacts and parsed
decisions live on GitHub; raw exchanges, transient progress and controller
state do not. "Full exchange on the ledger" → parsed exchange. Both now match
I2's tiering, which the rest of the paper already stated.

## Finding 6 — deployment evidence framed a notch too strongly. Accepted.

§4.2 now names the deployment an observational feasibility case study with no
control condition and no effectiveness claim; "behaviourally confirmed" is
defined at first use as closure evidence, not independent ground truth. The
closure-lag statistic already stated its denominator and the exclusion of the
three open findings.

## Minor items

Receipt authorship clarified in the loop figure's caption (derived by the
deterministic workflow, never authored by the model); "an afternoon" now
carries the configuration cost it previously omitted; the abstract states
the trial's scale and single-run nature (1,875 chars, still under the
1,920-character listing cap); reference [4] updated to the verified journal
version (Nature 655:487–496, 2026 — this reviewer's citation checked out
where the previous reviewer's link did not); tagged-PDF accessibility remains
deferred with the venue version, noted for the third time.

## Standing scoreboard

Three external reviews in two days; every finding verified before action;
resolved in code where code was the honest fix (verdict precedence, cluster
inference, hash manifest), in prose where the prose had outrun the system,
and deferred with reasons where the work belongs to the venue revision or the
registered study. The reviewer's own framing is adopted as the paper's:
a protocol and systems contribution with an existence proof, whose efficacy
question is registered, instrumented, and deliberately unanswered here.
