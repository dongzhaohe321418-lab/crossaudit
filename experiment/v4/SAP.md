# CrossAudit v4 — Statistical Analysis Plan

**Registered:** 2026-09-01
**Status:** prospective; no v4 outcomes inspected
**Authority:** companion to `REGISTRATION.md`. Conflicts are resolved in favour
of the registration, then this SAP, then the runbook.

## 1. Analysis populations

### 1.1 Controlled intention-to-audit population

All frozen controlled artefacts assigned to a confirmatory audit cell are
included. Empty, malformed, out-of-schema, rule-free, and auditor-refusal
responses remain in the population as escalations. A response is excluded only
for a documented infrastructure failure that occurred before any response bytes
were received, and it remains present as missing for sensitivity analysis.

### 1.2 Natural and real-task populations

All registered natural and replay tasks with locked Gold Panel labels are
included. Tasks whose human gold standard remains `unclear` after third-person
adjudication are excluded from binary accuracy analyses but retained in burden,
disagreement, and ordinal sensitivity analyses. Counts and reasons are reported
by domain and generator vendor before arm reveal.

### 1.3 Per-protocol sensitivity population

This excludes only calls with a pre-reveal, independently documented protocol
failure: wrong artefact hash, wrong model endpoint, wrong Constitution hash,
wrong DCL hash, non-fresh context, or leaked arm identity. It is secondary and
cannot replace the intention-to-audit result.

## 2. Units and clustering

- Randomisation unit for audits: artefact × auditor-vendor × Constitution cell.
- Primary observational unit: one audit reply on one artefact.
- Independent resampling unit: `task_id`.
- `base_artifact_id` nests clean/mutant siblings and generator outputs within a
  task.
- Three audit repeats are repeated measurements, not three independent tasks.
- Multiple defects in one artefact share one model response and are never
  treated as independent Bernoulli trials.
- Ledger-study reviewers and episodes are crossed random factors.

## 3. Derived outcomes

### 3.1 `correct_gate`

Gold `requires_block = true` and model/controller `BLOCK` yields 1. Gold
`requires_block = false` and `PASS`/non-blocking advisory yields 1. All other
combinations yield 0. Invalid audit integrity yields `ESCALATE` and 0 unless the
gold standard explicitly requires human escalation because evidence is
insufficient; that special class is reported separately and is not used to make
clean/defective balanced accuracy look better.

### 3.2 False block

`false_block = 1` when a verified clean or out-of-scope-only artefact receives
any effective model-originated BLOCK. DCL corpus-integrity failures on a nominal
clean artefact trigger the frozen mislabeled-clean procedure rather than being
charged to a model arm.

### 3.3 Finding validity and matching

Each finding may match at most one gold defect; each gold defect may receive at
most one primary catch per audit reply. A finding is valid if the Matching Panel
maps it to an existing gold defect or the Gold Panel confirms it as `valid_new`.
One verbose finding cannot discharge several defects. Evidence assembled from
several findings cannot be used to create a post-hoc catch.

### 3.4 Test–retest outcomes

- verdict flip: not all three repeats return the same effective gate;
- pairwise verdict agreement and chance-corrected agreement;
- finding overlap: Jaccard similarity over matched gold defect IDs;
- stable valid catch: caught in at least two of three repeats, reported as a
  sensitivity endpoint rather than replacing per-call intention-to-audit.

## 4. Primary estimands

### 4.1 Cross-vendor gate accuracy

Estimate the marginal standardised risk difference:

`Pr(correct_gate | cross) - Pr(correct_gate | same)`.

Standardisation gives equal weight to generator vendors, domains, controlled
clean/defective status, and registered model panels, regardless of technical
missingness or realised task counts.

The primary estimator is deliberately model-free and task-clustered. First
average the three independent repeats inside each exact
artefact×auditor×C2×D2 cell. Then average eligible artefacts within each
task×generator×auditor×registered target stratum. For task `t`, form

```text
C_t = 0.5 * (Y_A→B,t + Y_B→A,t)
    - 0.5 * (Y_A→A,t + Y_B→B,t)
```

The four `Y` values use equal weights over the registered domain, controlled
clean/defective, and model-panel target cells; empty target cells remain
missing rather than being silently reweighted. The point estimate is the mean
of `C_t`. A whole-task non-parametric bootstrap with at least 5,000 resamples
supplies the primary two-sided 95% interval. A task-level sign-flip/randomisation
interval and a pre-specified logistic mixed model followed by g-computation are
sensitivity analyses. The mixed model includes generator vendor, auditor
vendor, cross-vendor assignment, stratum, domain, repeat, the registered
cross×stratum interaction, task/base-artefact random intercepts, and a
model-panel random intercept only when more than one fully crossed panel exists.
Failure or non-convergence of the sensitivity model does not replace or alter
the registered model-free primary result.

The Question 1 superiority test uses alpha 0.05, two-sided. Direction is
interpreted only after the interval is computed.

### 4.2 Clean false-block non-inferiority

On verified clean and out-of-scope-only controls, use the same repeat collapse,
four-direction task contrast, fixed target weights, and whole-task bootstrap to
estimate:

`Pr(false_block | cross) - Pr(false_block | same)`.

Cross is non-inferior only if the upper bound of the one-sided 95% confidence
interval is below +0.05. Both raw direction-specific rates and exact binomial
intervals are also reported. Superiority on correct gate without this
non-inferiority result does not satisfy the headline claim.

## 5. Factorial ablation

The confirmatory ablation estimator repeats the task-standardised procedure at
each registered Constitution×DCL cell. Each contrast is a paired difference of
task-level arm means. The following mixed model is a sensitivity analysis:

```text
correct_gate ~ generator_vendor + auditor_vendor + cross_vendor
             + constitution + dcl
             + constitution:dcl
             + constitution:auditor_vendor
             + data_stratum + domain
             + (1 | task_id) + (1 | base_artifact_id)
```

Registered Constitution contrasts form one Holm family:

1. C0 vs C1;
2. C1 vs C2;
3. C0 vs C2.

Registered DCL contrasts form a second Holm family:

1. D0 LLM-only vs D2 combined-blind;
2. D1 DCL-only vs D2 combined-blind.

The C×D interaction is one pre-specified test at alpha 0.05. D3 routed results,
if run, are exploratory. Report marginal risk differences for correct gate,
false block, validated defect recall, and workload-standardised accuracy.

Channel decomposition uses exact set membership over gold defect IDs:
DCL-only catch, tool-only catch, LLM-only catch, overlaps, and defects caught by
none. It is descriptive unless a contrast above explicitly covers it.

## 6. Defect detection and finding precision

Validated BLOCKER-defect recall is first averaged within audit reply and then
within task; uncertainty comes from whole-task bootstrap resampling. A mixed
logistic sensitivity model uses task and artefact random intercepts, with defect
class/channel and their interaction with cross assignment as fixed effects.
The review-only stratum is reported separately and never pooled away by large
numbers of trivial DCL-visible defects.

Finding precision is:

`validated findings / all effective findings`.

Withdrawn self-corrections, passed checks, and deterministic referrals are
reported in their own denominators and are not allegations. Unknown-rule
citations remain effective findings for false-block burden and are also counted
as ungrounded. Precision and recall are always reported together with findings
per artefact.

## 7. Natural and real-task validation

Repeat the primary task-standardised contrast within each `data_stratum`; a
mixed model with stratum interactions is a sensitivity analysis. These strata
are key secondary analyses. A pooled cross effect is reported only if the
direction is not concealed by strong stratum heterogeneity; otherwise the
stratum-specific effects are the result.

Natural-defect recall requires the Gold Panel's exhaustive pre-audit defect
enumeration. If the reliability stop downgrades that enumeration, natural/real
analyses report finding precision and gate accuracy but do not claim exhaustive
recall.

## 8. Whole-loop analysis

The loop population is analysed at artefact level. Report by assigned audit
condition:

- resolved fraction of initial validated defects;
- probability final artefact is acceptable;
- new defects per artefact;
- unnecessary changes per artefact;
- compliance-only/harmful change proportions;
- revisions, escalation, calls, tokens, latency, and recorded human minutes.

Primary comparisons are paired task-level differences with whole-task
bootstrap intervals. Logistic, negative-binomial, Gamma-log, or log-normal
mixed models appropriate to binary, count, and skewed outcomes are sensitivity
analyses selected before reveal by blinded diagnostics. A net-correction
composite is descriptive unless its weights were added to the frozen manifest
before any loop output.

## 9. Defensive-production analysis

Policy P0/P1/P2 is randomised. Primary defensive endpoints are:

1. compliance-only plus defensive-disclaimer content as a proportion of changed
   content; and
2. independently blinded final task quality.

Secondary endpoints are words/LOC, file count, metadata proportion, wrappers,
retry scaffolds, exception branches, dependency additions, duplicate
assertions, novelty rating, escalation requests, held-out check performance,
cost, and latency. Primary policy comparisons average within generator session
and task and use a whole-session/task cluster bootstrap; mixed-model
sensitivities include policy, generator vendor, domain, and their registered
interactions, with task/session random intercepts.

Evidence for defensive production requires P1/P2 to increase compliance-only or
defensive content without a corresponding improvement in independent quality or
held-out generalisation. No conclusion follows from verbosity alone.

## 10. Ledger study analysis

Review sessions are randomised to E0/E1/E2 without exposing the same episode
under more than one surface within a session. A balanced Latin-square schedule
crosses reviewers and episodes across independent sessions. Primary
outcomes:

- correct accept/reject decision: reviewer-clustered risk difference with an
  episode-cluster sensitivity interval;
- time to correct decision: reviewer-clustered restricted-mean time contrast,
  counting incorrect/unresolved reviews at the registered cap.

Crossed logistic and survival models with reviewer and episode random effects
are sensitivity analyses.

Secondary outcomes are first-defective-commit identification, correct rule
version, tamper detection by attack class, confidence calibration, and burden.
E2 vs E0 is the primary ledger contrast; E2 vs E1 and E1 vs E0 are Holm-adjusted
secondary contrasts.

## 11. Multiplicity

The dual primary gate is conjunctive: both conditions must pass, so no alpha
split is required. Holm correction applies within the Constitution, DCL, and
ledger contrast families. Key secondary outcomes are reported with 95%
intervals and effect sizes; they do not rescue a failed primary. Exploratory
defect-taxonomy scans use Benjamini–Hochberg false-discovery control and are
labelled exploratory.

## 12. Missingness and invalid replies

Transport failure after the permitted byte-identical retries is missing, not a
PASS. The primary task-standardised estimator uses observed assigned calls
under the intention-to-audit rule without reweighting a missing target cell;
sensitivity analyses include:

1. cross failures incorrect, same failures correct;
2. cross failures correct, same failures incorrect;
3. all failures incorrect;
4. inverse-probability weighting using only pre-treatment task, domain, vendor,
   payload-size, and scheduled-order variables.

If missingness triggers a stopping threshold, no missing-data model restores a
confirmatory claim for that incomplete cohort.

## 13. Nominal-clean relabelling

The key remains frozen. If a genuine unseeded BLOCKER is found in a nominally
clean artefact:

- retain the original nominal-clean analysis;
- add a gold-corrected sensitivity analysis using the blinded Gold Panel's
  adjudication;
- report which arms surfaced it, without removing their findings as “false
  positives”; and
- if the pre-audit clean-validation procedure was not followed, treat that as a
  protocol deviation, not as evidence about auditors.

No artefact is deleted after reveal because its label became inconvenient.

## 14. Three-or-more-vendor analysis

For a complete V×V extension, include generator- and auditor-vendor fixed effects,
the cross indicator, and registered vendor-pair deviations. Report:

- included-vendor standardised cross effect;
- each directed generator→auditor contrast;
- heterogeneity interval/prediction display;
- leave-one-vendor-out estimates; and
- same-model, same-vendor-different-model, and cross-vendor contrasts where the
  nested model panel supports them.

With three vendors, vendor is still treated as fixed. A random-vendor population
claim is prohibited. With a sufficiently broad prospectively sampled set, a
random-vendor model may be registered in a new SAP before that cohort runs.

## 15. Analysis lock and reporting

Before unblinding:

1. validate manifests and hashes;
2. freeze all exclusions and deviations;
3. complete Gold/Matching Panel adjudication;
4. run analysis code on simulated data and blinded arm codes;
5. render shells of all primary and key secondary tables;
6. commit `PRIMARY-LOCK.json` containing hashes of code, data, tables, and this
   SAP; and
7. obtain an external timestamp/commitment.

After reveal, analysis code may be changed only to repair an execution bug.
Both original and corrected outputs remain, the bug and effect are disclosed,
and corrected analysis cannot silently replace the registered one.
