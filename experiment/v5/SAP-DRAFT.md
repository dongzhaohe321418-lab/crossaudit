# CrossAudit v5 — statistical analysis plan draft

**Status:** prospective and outcome-free; must be frozen with code and table
shells before provider dispatch.

## 1. Estimand

Within each task, collapse the three fresh-context repeats inside each exact
artefact x auditor x Constitution x DCL cell.  Apply fixed weights over domain,
task source, natural/controlled status, clean/defective status, mutation class,
detection channel, and model panel.  For generator vendor `g`, compute the mean
of its two cross-vendor auditor cells minus its matched-model cell.  Average
those three generator-specific contrasts equally:

```text
C_t = (1/3) * sum_g [ mean_{a != g}(Y_t,g,a) - Y_t,g,g ]
```

The reported primary estimate is the mean of `C_t` over tasks.  This is an
included-vendor fixed-panel estimand; three vendors do not identify a random
vendor-population effect.

The same construction on verified-clean artefacts estimates the cross-minus-
matched clean unnecessary-escalation risk difference.

## 2. Primary inference

- two-sided 95% whole-task bootstrap-t interval for `correct_gate`;
- one-sided 95% whole-task bootstrap-t upper bound for clean unnecessary
  escalation;
- at least 5,000 resamples in the locked analysis;
- a task-level wild/sign-flip cluster interval as a robustness check; and
- a logistic mixed-effects sensitivity model followed by marginal
  g-computation.

The sensitivity model uses task and base-artefact random intercepts and fixed
effects for generator model, auditor model, separation class, domain, stratum,
defect channel, and pre-specified separation interactions.  Vendor is fixed.
Non-convergence cannot replace the model-free result.

## 3. Planned comparisons

The dual primary gate is conjunctive, so no alpha split is used.  Mandatory
secondary contrasts are:

1. S1 same-vendor/different-model minus S0 matched-model;
2. S2 cross-vendor minus S1;
3. each directed generator-to-auditor contrast;
4. review-only and DCL-negative strata;
5. leave-one-vendor-out estimates; and
6. cost- and human-minute-standardised net correction.

C0/C1/C2 contrasts form one Holm family.  D0/D1/D2 contrasts form a second
Holm family.  Taxonomy scans use Benjamini-Hochberg FDR and remain exploratory.

## 4. Human labels and reliability

Gold and Matching Panels are separate.  One finding can match at most one gold
defect and one verbose finding cannot discharge several defects.  Natural
defect recall is reported only if exhaustive pre-audit enumeration passes the
calibration gate.  Otherwise the natural cohort supports gate accuracy and
finding precision, not exhaustive recall.

## 5. Whole-loop outcomes

The 60-task subset is paired before outcome access.  Same and cross branches
receive the same starting artefact, information, controller, and maximum of two
revision rounds.  Report initial-defect resolution, final acceptability, new
defects, unnecessary changes, compliance-only changes, calls, tokens, latency,
cost, and human minutes.  A net-benefit score is confirmatory only if all value
and cost weights are frozen before dispatch; otherwise the Pareto frontier is
reported without collapsing outcomes into one number.

## 6. Missingness and integrity

The service-level intention-to-audit analysis treats invalid, missing, or
identity-unverified assigned audits as incorrect gates and, on clean items, as
unnecessary escalations.  Sensitivities include complete-case, all-failures-
incorrect, direction-worst-case, and inverse-probability weighting using only
pre-treatment variables.  The analysis reports valid-call rate and missingness
by provider before efficacy estimates.

## 7. Reporting discipline

The abstract reports task, artefact, and human-reviewer counts before model-call
counts.  Raw direction-specific results accompany every pooled result.  The v4
feasibility cohort is shown only as machinery validation and is never pooled,
used for observed power, or cited as confirmation of efficacy.
