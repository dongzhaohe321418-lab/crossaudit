# Validation report: v5 design and central power simulation

## Overall assessment: Needs revision before dispatch

The prospective question, task-level estimand, three-vendor allocation, call
arithmetic, and central design simulation are internally consistent.  The
package is ready for design review, not provider dispatch: stress scenarios,
bootstrap-t calibration, resolved model identities, human-panel calibration,
privacy approval, randomisation commitments, and all cost caps remain absent.

## Methodology review

- The independent unit is `task_id`; audit repeats, clean/mutant siblings,
  principal-generator outputs, findings, and defects remain inside that unit.
- The primary panel contains three included vendors.  The estimator equally
  averages the two cross-auditor directions inside each Generator and then
  equally averages Generators.  The claim scope is therefore included
  configurations, not a vendor population.
- Same-model, same-vendor/different-model, and cross-vendor conditions are
  separated.  This removes the main ability/vendor confounding in v4.
- C0/C1/C2 each receive three repeats in the prospective cohort.  The v4
  repeat-0 diagnostic is not repaired or pooled.
- Service-level failures remain incorrect gates and clean unnecessary
  escalations; complete-case results are sensitivity analyses.

## Calculation spot-checks

- Planned calls: `450 + 12,150 + 4,050 + 6,480 + 1,800 = 24,930` (verified).
- Simulations: 10,000 central datasets (verified from machine-readable output).
- Nominal/marginal effect: 0.0800 / 0.079975 (difference -0.000025).
- Conjunctive power: 0.9965 (passes the 0.80 central design target).
- Two-sided coverage: 0.9487 (passes the registered 0.93--0.97 range).
- Directional superiority type-I error: 0.0249 (passes 0.015--0.035; the
  positive claim uses the lower tail of a two-sided 95% interval).
- Non-inferiority-boundary type-I error: 0.0475 (passes 0.04--0.06).
- The simulation reads no observed v4/v5 outcome file (code-path and output
  declaration checked; outcome independence is also a procedural commitment).

## Issues found

1. **High:** Only the central scenario has 10,000 simulations.  Dependence,
   direction reversal, auditor heterogeneity, missingness, low-accuracy, and
   high-false-block scenarios remain unrun.
2. **High:** The current design simulation uses a task-level normal interval.
   The exact locked bootstrap-t analysis needs at least 1,000-dataset coverage
   calibration before power is frozen.
3. **High:** Model snapshots, panel manifests, calibration report, privacy
   approvals, randomisation, external timestamp, and budget fields are null.
   `preflight.py` correctly refuses dispatch.
4. **Medium:** Natural-defect prevalence and latent dependence are planning
   assumptions, not estimates.  They must be frozen from outcome-independent
   external evidence or covered by stress scenarios.
5. **Medium:** The power result addresses the co-primary gate, not precision for
   Constitution, whole-loop, defensive-production, or human-ledger modules.
   Those modules remain secondary unless separately powered.

## Reproducibility bindings

- `power-central-10000.json` SHA-256:
  `51b375f69f5b0916321d06d4692074bc4894dbefbf9312834eb2fb1e4411aee7`
- `power_simulation.py` SHA-256:
  `daa0ae97dff0a5fbf5c1b4bdbe92225a5fd2adec7d14b57504b9a69a0707b5a6`
- `config/study.yaml` SHA-256:
  `f64b3cd6f9251f662c1d74d4828031e29e2caba762b6fdf52345784f8203569a`

These hashes document the current design iteration.  They are not the final
external timestamp or dispatch freeze.
