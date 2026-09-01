# V4 feasibility figures

These figures are generated from the sealed Amendment 2 feasibility summary with
Python only. They are descriptive, non-confirmatory, and configuration-specific.
They do not support a vendor-population claim.

## Figure contracts

### Figure 5: configuration- and component-specific effects

- **Core conclusion:** the average cross-minus-same result is not a universal
  cross-vendor advantage. Its magnitude and direction depend on the author--auditor
  configuration, and the apparent D2 gain over D0 is localized to the natural-output
  stratum.
- **Results question:** which pairing directions and audit components account for
  the observed correct-gate and false-block differences?
- **Archetype and final size:** four-panel quantitative grid, double-column width
  (183 mm), 183 x 126 mm.
- **Panel roles:** (a) absolute C2/D0 correct-gate rates for the frozen 2 x 2
  Generator--Auditor cells; (b) task-clustered pairing contrasts with descriptive
  bootstrap intervals; (c) task-clustered DCL contrasts on an improvement-positive
  scale; (d) natural versus controlled-strata decomposition, with D1 shown only as
  a checker-defined ceiling.
- **Statistics:** estimates and descriptive 95% task-bootstrap intervals use six
  deterministic convenience-task clusters. False-block contrasts are sign-reversed
  only where explicitly labelled "reduction" so that positive always means better.
- **Source:**
  `experiment/v4/feasibility/results/2026-09-01-six-task-amendment-2/summary.json`.
- **Reviewer risks:** tiny convenience cohort; no human adjudication; D1 shares the
  deterministic checker that defines micro-task gold; absolute cell color is
  redundant with printed values; intervals are descriptive, not confirmatory.

### Figure 6: operational gains, costs, and unresolved boundaries

- **Core conclusion:** hard-gate feedback repaired some initially wrong text outputs,
  but required materially more calls, cost, and provider time; same- and cross-audit
  whole-loop outcomes were identical in this cohort, and the structured ledger did
  not improve primary proxy decisions over an ordinary log.
- **Results question:** what operational benefits and liabilities accompany the
  stronger audit interfaces?
- **Archetype and final size:** four-panel quantitative grid, double-column width
  (183 mm), 183 x 126 mm.
- **Panel roles:** (a) initial-to-final objective correctness for P0/P1/P2;
  (b) calls, list-price-equivalent cost, and cumulative provider time relative to
  P0; (c) paired same/cross whole-loop endpoints; (d) E0/E1/E2 ledger-proxy decision
  and reconstruction accuracy.
- **Statistics:** text-policy points are 12 sessions per arm over six task clusters;
  whole-loop points are 12 branches per assignment over six task clusters; ledger
  points are 14 proxy reviews per interface clustered in seven deterministic
  episodes. No bar or point is treated as an independent replicate for inference.
- **Source:** the same sealed `summary.json`; the 5/96 three-repeat gate-flip
  diagnostic is reported in the legend rather than promoted to an extra panel.
- **Reviewer risks:** endpoint bars overlap conceptually and are not compositional;
  ledger participants are fresh model proxies rather than humans; capped decision
  time is not human review time; OpenAI calls expose only an alias and remain
  identity-unverified.

The Constitution ablation is deliberately excluded. The frozen scorer uses
`repeat == 0` for that contrast, while the registration text says that C2 uses the
three core repeats. Until that estimand mismatch is resolved, the existing
Constitution summary must not be presented as a three-repeat-collapsed effect.

## Reproduce

Install `nature-figure` and `nature-shared` from
<https://github.com/Yuan1z0825/nature-skills> at the revision used here,
`ebd722e18808442688bd205917a3e774195c258f`, then run:

```bash
uv run --no-project --python 3.12 \
  --with-requirements experiment/v4/figures/requirements.txt \
  python experiment/v4/figures/plot_feasibility.py
```

The script asserts the freeze digest, completion counts, and structural validity;
writes `source-data.csv`; exports PDF/SVG/PNG/TIFF to `paper/figures/`; and runs the
mandatory 1.5 pt Matplotlib panel-alignment gate. Rendered PDF font and collision
audits are recorded under `qa/` by:

```bash
uv run --no-project --python 3.12 \
  --with-requirements experiment/v4/figures/requirements.txt \
  python experiment/v4/figures/run_qa.py
```

The human panel-by-panel inspection record is in `QA-NOTES.md`; the machine-readable
aggregate result is `qa/qa-summary.json`.
