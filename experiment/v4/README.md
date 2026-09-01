# CrossAudit v4 Causal Successor Study

This directory holds the prospective design for the **CrossAudit v4 Causal
Successor Study**, registered 2026-09-01 before any v4 arm ran or any v4 outcome
was inspected.

It is a successor, not an amendment. The finished v1 pilot and the frozen v2/v3
registrations remain where they are and retain their original authority. v4 is
designed to answer causal and operational questions those studies could not.

## What v4 adds

1. a complete generator-vendor × auditor-vendor 2×2 in both directions;
2. DCL and no/generic/decidable-Constitution ablations;
3. a randomised defensive-production study;
4. controlled seeded, natural-defect, real-task, and clean-control strata;
5. a bounded whole-loop revision study;
6. a randomised third-party ledger-value study; and
7. three audit repeats, blinded human ground truth, task-clustered inference,
   prospective power, and fixed stopping rules.

The complete acceptance contract is `SEVEN-POINT-COMPLETION.md`.

## Authority and reading order

1. `REGISTRATION.md` — questions, interventions, data, endpoints, blinding,
   claim boundaries, and freeze rules.
2. `SAP.md` — analysis populations, estimands, models, multiplicity,
   missingness, and sensitivity analyses.
3. `POWER.md` — eight-point smallest effect, 120-task initial design, 180-task
   cap, three repeats, simulation, and blinded sample-size re-estimation.
4. `STOPPING-RULES.md` — integrity, model-drift, technical, human-reliability,
   privacy, and cost stops.
5. `RUNBOOK.md` — execution order and operator gates.
6. `config/` and `constitutions/` — machine-readable design and registered
   rulebook levels.

On conflict, the order above applies. None of these documents can change a
frozen v1–v3 record.

## Current status

**NOT YET RUN.** The documentation is registered, but the study is not dispatch
ready. The following are intentionally null and blocking:

- exact provider endpoints and model snapshots;
- randomisation seed commitment and blinded vendor-code custody;
- corpus/task manifest and external ground-truth/defect commitments;
- ablation, revision, defensive, and ledger module sample sizes;
- complete power-simulation output;
- maximum calls, tokens, money, wall time, and human-review hours; and
- panel membership/calibration and privacy approvals.

The operator must freeze these fields without looking at v4 outcomes. A null
field is not a default.

## Minimum causal core

Every task is independently completed by generator A and generator B. Every
artefact is audited by both auditor A and auditor B, three times each in fresh
contexts. The same artefact therefore supplies a paired same-vendor and cross-
vendor audit.

The primary result is the standardised difference in correct-gate probability,
subject to a +5 percentage-point clean false-block non-inferiority gate. Raw
recall, BLOCK rate, and finding count cannot establish success.

With two vendors the claim is configuration-specific. A three-or-more-vendor
extension must complete the full V×V matrix and may generalise only to the
included vendors. Population-level vendor claims require a broader prospective
sample or meta-analysis.

## Dispatch principle

The eventual validator must fail closed unless all required fields are concrete,
all files match the freeze manifest, every task has complete same/cross
assignments, and cost/privacy gates are satisfied. Execution happens by opaque
randomised blocks. No arm output is opened until its block is complete, and no
analyst sees the arm mapping before `PRIMARY-LOCK.json` is committed.

Secrets, plaintext defect keys, gold-label mappings, protected real-task data,
and provider credentials never enter this public directory.

## Honest result language

Allowed for a completed two-vendor cohort:

> For these pinned generator and auditor configurations, tasks, prompts, and
> dates, cross-vendor assignment changed correct-gate probability by …

Not allowed:

> Cross-vendor auditing is generally superior.

Passing process checks is not a certification that a scientific conclusion is
true. A receipt is hash-bound evidence of what the controller recorded, not
provider-signed proof of model identity unless such an attestation actually
exists.
