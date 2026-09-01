# CrossAudit v4 — Prospective Power Plan

**Registered:** 2026-09-01
**Status:** design values registered; simulation and nuisance inputs not yet
frozen. No v4 result may be used to choose them.

## 1. Smallest effects and design limits

- Primary superiority smallest effect of interest: **8 percentage points** in
  standardised `correct_gate` probability, cross minus same.
- Clean false-block non-inferiority margin: **+5 percentage points**.
- Initial task-brief count: **120**.
- Hard maximum after the single blinded re-estimation: **180**.
- Independent audit repeats per artefact × auditor × Constitution cell: **3**.
- Confirmatory minimum: complete two-vendor 2×2 in both directions.

The task, not the individual defect or repeated call, is the independent power
unit.

## 2. Analytic orientation

For a paired binary comparison with discordant probability approximately 0.25,
80% power, two-sided alpha 0.05, and an eight-point difference, the simple
McNemar approximation is

\[
n\approx\frac{(1.96+0.84)^2\,0.25}{0.08^2}\approx307
\]

independent paired artefacts. This is an orientation, not the final calculation:
clean/mutant siblings, generator outputs, domains, and three repeats are
clustered within tasks.

Under the planned controlled construction, 120 briefs × two generators × one
clean and one mutant yields up to 480 artefact-level same/cross pairs. A design
effect near 1.6 would leave roughly 300 independent-pair equivalents. These are
assumptions to be stress-tested, not claimed empirical facts.

## 3. Required simulation before dispatch

The frozen power script must simulate the exact allocation and registered
task-standardised estimator in `SAP.md` for at least 10,000 datasets per
scenario. Any mixed-model sensitivity is not used to declare design power. The
simulation must vary:

- same-vendor correct-gate probability: 0.60, 0.70, 0.80;
- cross-vendor risk difference: 0, 0.05, 0.08, 0.10;
- clean false-block baseline: 0.02, 0.05, 0.10, 0.20;
- task/base-artefact ICC: 0.10, 0.20, 0.30;
- repeat-level correlation: 0.20, 0.50, 0.80;
- cross-direction heterogeneity and generator/auditor main effects;
- domain imbalance within the limits allowed by the randomiser;
- technical missingness: 0%, 2%, and 5%, including vendor-differential failure;
- natural unseeded defects in nominally clean candidates; and
- three-vendor extension scenarios, if that cohort is to run.

For each scenario report:

- superiority power and type-I error;
- false-block non-inferiority power and type-I error;
- probability both headline gates pass;
- convergence/failure rate of the analysis model;
- bias and coverage of the standardised risk difference; and
- impact of the planned bootstrap and missing-data sensitivity analyses.

The design proceeds at N=120 only if the central registered scenario reaches at
least 80% conjunctive power and type-I error remains controlled. Otherwise the
initial frozen N may be increased before calls, up to 180. If even N=180 fails,
the primary study must be described as estimation-focused or redesigned before
execution; it must not run underpowered and later change the smallest effect.

## 4. Blinded sample-size re-estimation

One re-estimation is allowed after 50% of the initially frozen task briefs have
completed all confirmatory cells. The statistician receives pooled, arm-masked
data and may estimate only:

- overall outcome prevalence;
- paired discordance without same/cross direction;
- task/base ICC;
- repeat reliability;
- technical missingness; and
- realised clean/defective balance.

The statistician cannot access vendor mappings, cross/same labels, directional
cell means, findings, or effect estimates. The pre-frozen simulation function
maps nuisance estimates to one of two actions:

1. retain the initial N; or
2. increase to the smallest permitted block size at or below 180 that restores
   target power.

No reduction below the initial frozen N is allowed. No second re-estimation is
allowed. The blinded input, decision, and function hash are committed before
unblinding.

## 5. Secondary-module sizing

The Constitution ablation subset, whole-loop subset, defensive-production
sessions, real-task replay, and ledger-reviewer experiment each require their
own prospective simulation or precision target. Their sizes are blocking null
fields in `config/study.yaml`; they cannot be inferred from unused primary
budget after results are visible.

Suggested planning targets, not yet frozen results or sample sizes:

- Constitution ablation: power the C1 vs C2 clean false-block contrast and
  balance every domain/stratum/vendor cell;
- whole loop: power final acceptability and estimate new-defect rate with a
  useful interval;
- defensive production: cluster at generator session and task, not output
  line;
- ledger study: cross reviewer and episode effects and power E2 vs E0 for both
  accuracy and time.

Any module that lacks its required frozen size before its first output is
exploratory by definition.

## 6. Cost and feasibility gate

Before dispatch the operator must freeze:

- maximum model calls by module and cell;
- maximum input/output tokens;
- maximum monetary spend in one named currency;
- maximum wall-clock duration;
- maximum human adjudication hours; and
- a reserve policy for permitted technical retries.

Power does not authorise exceeding those caps. If the powered design does not
fit the frozen feasible budget, the study is not ready to run. It is prohibited
to drop an unfavourable vendor direction, clean controls, or repeats merely to
fit cost after outputs exist.

## 7. Reporting

Publish the simulation code, seeds, complete scenario grid, convergence
diagnostics, and machine-readable results before model-arm reveal. Report the
achieved task and artefact counts as design execution, never as post-hoc power.
Observed-power calculations are prohibited.
