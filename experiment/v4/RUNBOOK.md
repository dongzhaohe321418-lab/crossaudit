# CrossAudit v4 — Prospective Runbook

**Registered:** 2026-09-01
**Status:** not dispatch-ready; required freeze fields remain null.
**Protocol authority:** `REGISTRATION.md` → `SAP.md` → `POWER.md` →
`STOPPING-RULES.md` → this runbook.

This is an execution order, not evidence that any step has occurred. Boxes stay
unchecked until their hash-bound deliverables exist.

## Stage 0 — Preserve earlier studies

- [ ] Confirm v1 results and v2/v3 registrations are read-only inputs.
- [ ] Record their SHAs; do not move, re-score, or amend them from v4.
- [ ] Create a dedicated v4 cohort ID and output namespace.
- [ ] Confirm no v4 output exists. If it does, this registration cannot be called
      prospective for that cohort.

## Stage 1 — Freeze governance and feasibility

- [ ] Name the principal, independent key custodian, blinded statistician, Gold
      Panel, Matching Panel, and ledger reviewers.
- [ ] Record qualifications, conflicts, and data-access boundaries.
- [ ] Complete privacy/licence review for every real-task snapshot.
- [ ] Freeze exact call, token, money/currency, wall-time, human-hour, and retry
      caps in `config/study.yaml`.
- [ ] Freeze study deadline and incident contacts.
- [ ] Verify the powered design fits the caps. If not, redesign before calls;
      do not drop a vendor direction or clean controls after outputs.

## Stage 2 — Lock providers and models

- [ ] Fill `config/models.lock.json` with exact vendor, endpoint, API version,
      model snapshot, region, tool policy, parameters, context limits, and
      retention claims supported by provider documentation.
- [ ] Verify both vendors can act as Generator and Auditor.
- [ ] Verify fresh-context and tool-isolation behaviour with non-study canaries.
- [ ] Verify model identities are stable enough to pin.
- [ ] Revoke any credential ever exposed in chat/logs and install new secrets in
      the approved runner; never write them to the repository.
- [ ] Hash and externally timestamp the lock.

If models are still placeholders, stop here.

## Stage 3 — Freeze tasks, corpora, and keys

- [ ] Freeze at least 120 task briefs, evenly blocked across the registered
      domains, plus at least 60 natural/real task briefs.
- [ ] Record immutable input manifests, licences, privacy class, and intended
      stratum before generation.
- [ ] Generate each controlled/natural task independently through every pinned
      Generator; retain request/response hashes and actual provider request IDs.
- [ ] Run deterministic/domain checks on candidate controlled bases.
- [ ] Gold Panel blindly validates candidate clean bases. Non-clean candidates
      move to natural; they are never silently repaired and labelled clean.
- [ ] Produce one clean and one single-target mutant per eligible base.
- [ ] Validate target mutation, exact location, severity, scope, Constitution
      coverage, and cheapest catching channel.
- [ ] Build unusual-but-correct and out-of-scope negative controls.
- [ ] Escrow plaintext defect/gold mappings externally and commit only an
      independently useful encrypted/escrow commitment.
- [ ] Freeze corpus/split/input manifests and scrubber hash.

No auditor call occurs before all controlled clean labels and defect mappings
are committed to custody.

## Stage 4 — Freeze interventions and analysis

- [ ] Finalise and length/concept-match C0/C1/C2; record hashes.
- [ ] Freeze D0/D1/D2 controller synthesis and optional D3 routing policy.
- [ ] Freeze common auditor reply schema and provider wrappers.
- [ ] Freeze generator prompts and P0/P1/P2 disclosure text.
- [ ] Freeze whole-loop round limit and feedback packaging.
- [ ] Freeze ledger E0/E1/E2 surfaces, reviewer time cap, and attack key.
- [ ] Freeze matching/adjudication manual and run independent calibration.
- [ ] Run the full analysis pipeline on simulated and opaque canary data.
- [ ] Run `POWER.md` simulation, freeze initial N, and select all module subsets
      prospectively.
- [ ] Freeze the randomisation algorithm and seed commitment. Keep seed and arm
      map from operators who can inspect outputs.
- [ ] Create the externally timestamped freeze manifest.

## Stage 5 — Dispatch validator

Run the results-independent configuration gate before constructing any
results-shaped export:

```bash
python experiment/v4/preflight.py experiment/v4
```

It must exit non-zero while a required governance, model, cap, custody or
privacy field is unresolved. Passing this narrow gate does not authorise a
call; the frozen corpus/schedule must then pass `validate_dataset.py` with
`--dispatch-freeze-root`.

The eventual validator must exit non-zero if any condition fails:

- required study/model field is null, placeholder, or unhashed;
- files differ from the freeze manifest;
- task/cell counts are incomplete or imbalanced beyond frozen blocks;
- a task lacks either generator direction or same/cross auditor cell;
- a model-call cell lacks exactly three scheduled repeats;
- Constitution/DCL/subset assignments are inconsistent;
- key/gold/arm-map custody proof is absent;
- privacy approval or numeric cost caps are absent; or
- a prior v4 output predates the freeze.

Commit the validator report before calls.

## Stage 6 — Run deterministic channels

- [ ] Run frozen DCL/domain tools once per artefact and write immutable raw
      output plus tool/environment hashes.
- [ ] Do not reveal defect keys to validate catches.
- [ ] A clean candidate with a new deterministic failure follows the corpus-
      quality rule; it is not patched after arm execution begins.
- [ ] Preserve DCL-only outcomes for D1 and controller synthesis for D2.

## Stage 7 — Run confirmatory 2×2

- [ ] The randomiser emits opaque blocks with equal A→A, A→B, B→A, B→B
      schedules and three repeats.
- [ ] The scrubber verifies absence of origin metadata without rewriting content.
- [ ] Each audit starts in a fresh context with the same output contract, tools,
      token budget, and assigned C2 rules.
- [ ] D2 auditors do not see DCL results.
- [ ] Persist request/response hashes, provider request ID, parse result, costs,
      timings, assignment code, and input manifest.
- [ ] Apply at most two byte-identical retries to transport failures only.
- [ ] Treat malformed/refused content as an outcome, not a retry opportunity.
- [ ] Monitor only integrity, technical health, cost, and balance. Do not inspect
      arm findings or verdict distributions.
- [ ] Close and hash each block before the next.

Any stopping event follows `STOPPING-RULES.md` and is recorded before resume.

## Stage 8 — Run registered ablation

- [ ] Use only the prospectively frozen balanced subset.
- [ ] Run C0/C1/C2 for all included auditor vendors with three repeats.
- [ ] Reconstruct D0/D1/D2 from the same LLM reply/DCL run where registered.
- [ ] If D3 is run, use separate calls and label it exploratory.
- [ ] Preserve unknown-rule citations, withdrawals, referrals, malformed replies,
      and all findings.
- [ ] Do not tune C2 or DCL from observed arm behaviour.

## Stage 9 — Run natural and real-task shadow cohorts

- [ ] Execute the complete vendor matrix on immutable task replays.
- [ ] Never admit outputs downstream or modify live repositories.
- [ ] Gold Panel completes exhaustive blind labels without findings.
- [ ] Matching Panel receives pooled anonymous findings only after gold lock.
- [ ] Valid-new findings return blindly to Gold Panel.
- [ ] Close adjudication and reliability report before arm reveal.

## Stage 10 — Run whole-loop and defensive modules

- [ ] Use frozen prospective subsets and fresh sessions.
- [ ] Randomise P0/P1/P2 without policy crossover in one session.
- [ ] Execute maximum two revision rounds; preserve every parent/new artefact.
- [ ] Record findings supplied, changes, calls, tokens, latency, escalation, and
      human minutes.
- [ ] Blind reviewers label repair, regression, unnecessary work, defensive
      content, novelty, independent quality, and held-out-check performance.
- [ ] Do not use audit pass rate as the independent quality label.

## Stage 11 — Run ledger reviewer experiment

- [ ] Freeze episodes and E0/E1/E2 surfaces before allocation.
- [ ] Commit attack key externally.
- [ ] Randomise reviewer/episode/surface blocks so no reviewer sees the same
      episode twice.
- [ ] Record accept/reject, evidence cited, first bad commit, rule version,
      tamper calls, confidence, time, and burden.
- [ ] Keep reviewers blind to attack and study hypotheses.

## Stage 12 — Blinded sample-size checkpoint

- [ ] At 50%, export only pooled arm-masked nuisance data to the blinded
      statistician.
- [ ] Apply the pre-frozen mapping in `POWER.md` once.
- [ ] Commit input, function hash, and retain/increase decision.
- [ ] Never reveal directional means and never exceed 180 task briefs.

If the checkpoint cannot remain blind, retain initial N; do not improvise.

## Stage 13 — Primary lock and reveal

- [ ] Complete all Gold/Matching labels, deviations, missingness reasons, and
      exclusions while arm codes remain opaque.
- [ ] Run analysis code on blinded codes and render table/figure shells.
- [ ] Commit `PRIMARY-LOCK.json` with hashes of data, code, adjudication, SAP,
      exclusions, deviations, and table shells.
- [ ] Obtain an external timestamp.
- [ ] Only then reveal arm/vendor mappings and execute the frozen tables.

## Stage 14 — Report everything

- [ ] Primary superiority and false-block non-inferiority, regardless of result.
- [ ] Both cross directions and all four 2×2 cells.
- [ ] Repeat instability, invalid replies, unknown-rule use, and costs.
- [ ] C/D ablations and channel decomposition.
- [ ] Natural/real validation and adjudicator reliability.
- [ ] Whole-loop repair/regression/unnecessary work.
- [ ] Defensive and ledger modules.
- [ ] Missing-data, nominal-clean relabelling, and per-protocol sensitivities.
- [ ] Every stop, drift, cap, and deviation.
- [ ] Claim scope: pair-specific for two vendors; included-vendors-only for a
      complete 3+ vendor matrix.

Mark every row of `SEVEN-POINT-COMPLETION.md` COMPLETE, INCOMPLETE, or
EXPLORATORY with immutable links. Null and adverse results remain results.
