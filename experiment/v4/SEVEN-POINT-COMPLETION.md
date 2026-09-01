# CrossAudit v4 — Seven-Point Completion Contract

**Registered:** 2026-09-01
**Current state:** design documents created; all empirical completion boxes are
unchecked because v4 has not run.

This file turns the seven proposed improvements into acceptance tests. “Done”
means every required deliverable exists, validates, and is reported regardless
of direction. A paper paragraph, an illustrative run, or an unbalanced subset
does not satisfy a point.

## Global preconditions

- [ ] `config/models.lock.json` has concrete, pinned snapshots for every cell.
- [ ] `config/study.yaml` contains no null `required_before_dispatch` value.
- [ ] task/corpus, prompts, schemas, scrubber, DCL, tools, Constitutions,
      randomiser, scorer, power script, and analysis code are hash-bound in one
      externally timestamped freeze manifest.
- [ ] defect/gold/attack keys and arm mapping are committed to independent
      custody before relevant calls.
- [ ] power simulation supports the frozen N; initial N is 120 task briefs and
      may reach at most 180 through the single blinded procedure.
- [ ] exactly three independent audit repeats are scheduled for every required
      artefact × auditor × Constitution cell.
- [ ] call/token/money/time/human-hour caps and privacy policy are numeric and
      frozen.
- [ ] no v4 outcome was inspected before these gates passed.

## Point 1 — Genuine generator × auditor causal factorial

**Original requirement:** run a true same-vendor versus cross-vendor comparison,
not a deterministic corpus merely labelled with a notional generator.

### Required deliverables

- [ ] Every task has artefacts actually generated through the pinned A and B
      generator endpoints, with request/response provenance hashes.
- [ ] Within each vendor's core diagonal, Generator and Auditor use the same
      pinned model snapshot in fresh role-specific contexts; any same-vendor-
      different-model arm is secondary and separately labelled.
- [ ] Every A-generated artefact has A-auditor and B-auditor cells.
- [ ] Every B-generated artefact has A-auditor and B-auditor cells.
- [ ] Both directions have equal planned counts inside domain/stratum blocks.
- [ ] Auditors receive opaque, scrubbed artefacts and no generator transcript,
      provider identity, defect count, or other arm output.
- [ ] Every required cell contains three fresh-context repeats or a documented
      missing call under the stopping rules.
- [ ] The primary paired/clustered standardised risk difference and clean
      false-block non-inferiority result are published.
- [ ] Results are reported by direction, not only as a pooled cross average.

### Acceptance rule

Point 1 is complete only if the full 2×2 and both headline gates are analysed
under intention-to-audit. If only two vendors run, the result is labelled
`pair_specific`. A 3+ vendor extension is complete only with a full V×V matrix,
included-vendor heterogeneity, and leave-one-vendor-out results. No population-
vendor claim is permitted from two or three vendors.

## Point 2 — DCL and Constitution ablation

**Original requirement:** determine which component contributes value, including
DCL on/off and no/broad/decidable rulebooks.

### Required deliverables

- [ ] C0, C1, and C2 are frozen, hash-bound, concept-matched, rule-ID-matched,
      and approximately token-length-matched.
- [ ] D0 LLM-only, D1 DCL-only, and D2 combined-blind are derivable on the same
      artefacts; optional D3 routed is labelled exploratory.
- [ ] The ablation subset is selected prospectively and balanced by generator,
      auditor, domain, data stratum, clean/defective status, and defect channel.
- [ ] Each model-call Constitution cell has three repeats.
- [ ] C0→C1, C1→C2, C0→C2, D0→D2, and D1→D2 contrasts are reported with their
      registered multiplicity correction.
- [ ] The C×D interaction, workload-standardised effects, and DCL/tool/LLM
      exclusive/overlapping catches are reported.
- [ ] Unknown-rule citations, referrals, withdrawals, invalid replies, false
      blocks, and finding volume are retained rather than filtered away.

### Acceptance rule

Point 2 is incomplete if channels are compared on different artefacts, if C2
adds defect families absent from C1, or if only raw recall is reported.

## Point 3 — Defensive production and Goodhart measurement

**Original requirement:** measure whether hard audit causes a generator to
optimise for passing the reviewer rather than for the task.

### Required deliverables

- [ ] Fresh sessions are randomised to P0 unaware, P1 shadow-aware, and P2 hard
      gate using frozen disclosure text.
- [ ] Task blocks, generator vendors, and domains are balanced across policies.
- [ ] Independent blind reviewers score final task quality and method novelty.
- [ ] Added content is labelled `functional_improvement`, `necessary_evidence`,
      `compliance_only`, `defensive_disclaimer`, `neutral`, or `harmful`.
- [ ] Words/LOC, files, metadata share, wrappers, duplicate assertions,
      disclaimers, escalations, cost, and latency are reported.
- [ ] Held-out semantically equivalent checks measure rule-surface overfitting.
- [ ] P0/P1/P2 effects are estimated with task/session clustering and reported
      even if no defensive effect appears.

### Acceptance rule

Point 3 is complete only when compliance growth is evaluated beside independent
quality. Length alone is not defensive production, and higher audit pass rate is
not an independent quality measure.

## Point 4 — Controlled, natural, real, and clean evidence

**Original requirement:** do not rely only on template-generated seeded defects.

### Required deliverables

- [ ] Controlled corpus contains verified clean/mutant siblings with one target
      mutation, unique defect IDs, locations, severities, scopes, and channels.
- [ ] Natural corpus contains unmodified outputs from at least 60 frozen real
      task briefs, balanced by generator and domain.
- [ ] Real-task replay uses immutable, privacy-reviewed snapshots in isolated
      shadow environments and never alters a live science repository.
- [ ] Clean controls include ordinary and unusual-but-correct hard negatives.
- [ ] Gold Panel labels natural/real/clean artefacts before seeing findings.
- [ ] Matching Panel maps anonymous findings after gold enumeration; valid new
      findings return blindly to Gold Panel.
- [ ] Two reviewers plus a third-person resolution path and reliability
      intervals are reported.
- [ ] Nominal-clean defects are retained under both nominal and corrected-label
      analyses rather than deleted.

### Acceptance rule

Point 4 is incomplete if later generator compliance is treated as ground truth,
if clean means merely “no seeded mutation”, or if natural recall is claimed from
adjudicating only the findings auditors happened to emit.

## Point 5 — Whole-loop net outcome

**Original requirement:** evaluate the full generate–audit–revise loop, not only
whether a reviewer emits findings.

### Required deliverables

- [ ] A prospective balanced subset enters an immutable, maximum two-revision
      loop with frozen audit assignment.
- [ ] Every round records parent artefact hash, findings supplied, patch/new
      artefact hash, receipt, calls, tokens, time, and escalation.
- [ ] Blind reviewers label resolved initial defects, remaining defects, new
      defects, unnecessary changes, compliance-only changes, and harmful changes.
- [ ] Final acceptability, resolved fraction, new-defect rate, and unnecessary-
      change rate are co-reported.
- [ ] Human attention is recorded in minutes under a frozen collection method.
- [ ] No composite net score is headline unless its weights were frozen before
      the first loop output.

### Acceptance rule

Point 5 is incomplete if “finding acknowledged”, “file changed”, or “later
marked fixed” substitutes for independent verification that the defect was
resolved without regression.

## Point 6 — Ledger utility experiment

**Original requirement:** validate the Git ledger through reviewer performance,
not through auditor defect recall.

### Required deliverables

- [ ] Episodes are frozen with E0 final-only, E1 transcript, and E2 structured-
      ledger surfaces of matched information provenance.
- [ ] Reviewers are randomised so nobody sees multiple surfaces for one episode.
- [ ] Reviewers and episodes are crossed/balanced using a frozen allocation.
- [ ] Stale receipt, wrong commit, changed rulebook, missing round, altered
      report, and unsupported identity challenges are seeded and externally
      committed before review.
- [ ] Correct accept/reject decision and time to correct decision are primary.
- [ ] First-defective-commit, applicable-rule-version, per-attack detection,
      confidence calibration, and burden are reported.
- [ ] E2 vs E0 and secondary contrasts follow the registered mixed models and
      correction.

### Acceptance rule

Point 6 is incomplete if the structured ledger merely gives reviewers more
substantive evidence than comparison surfaces without disclosure, or if ledger
value is inferred from how many findings an LLM emitted.

## Point 7 — Repetition, blinding, inference, power, and stopping

**Original requirement:** replace one-run, defect-level inference with a
reliable, blinded, task-clustered confirmatory design.

### Required deliverables

- [ ] Three independent audit repeats per required cell; verdict flips and
      finding overlap reported.
- [ ] Opaque vendor/arm codes and artefact IDs remain sealed through
      adjudication and primary code/table lock.
- [ ] Gold and Matching Panels are independent of arm assignment; calibration
      reliability and disagreement are reported.
- [ ] Primary task-standardised cross-minus-same estimator, whole-task cluster
      bootstrap, paired robustness analysis, mixed-model sensitivity, and
      missing-data sensitivities run as registered.
- [ ] Power simulation covers effect, ICC, repeat correlation, direction
      heterogeneity, false-block rate, and differential missingness.
- [ ] Initial 120-task and hard 180-task limits are honoured; any increase uses
      the single blinded nuisance-only procedure.
- [ ] No efficacy/futility peeking occurs; every pause/stop has a structured
      record under `STOPPING-RULES.md`.
- [ ] `PRIMARY-LOCK.json` hashes data, analysis code, exclusions, adjudication,
      and table shells before arm reveal.
- [ ] Null, adverse, incomplete, and model-drift outcomes remain published.

### Acceptance rule

Point 7 is incomplete if individual defects or repeats are treated as
independent tasks, if arm identities are revealed before adjudication/analysis
lock, or if the sample is extended after looking at the effect.

## Completion declaration

The eventual completion statement must list each point as `COMPLETE`,
`INCOMPLETE`, or `EXPLORATORY`, link its immutable deliverables, and identify
the commit/freeze manifest. A point cannot be declared complete by editing this
checklist alone; the underlying evidence must validate.
