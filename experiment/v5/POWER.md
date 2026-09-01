# CrossAudit v5 — power and operating-characteristic requirements

The power simulation mirrors the planned allocation rather than multiplying
generation and audit repeats.  Every simulated task contains three generator
vendors, clean/mutant siblings, a complete 3 x 3 principal-auditor matrix, one
same-vendor alternate auditor per generator, and three audit repeats.  Task and
base-artefact latent effects and repeat correlation are separate.

The central design uses N=150, an eight-point included-vendor standardised
`correct_gate` effect, a +5-point clean-burden non-inferiority margin, and no
assumed cross-vendor clean-burden increase.  The one permitted blinded sample-
size re-estimation can increase N to 180 but never decrease it.

At least 10,000 datasets are required for each frozen scenario.  The minimum
scenario set is:

- central;
- high task/base dependence;
- severe repeat dependence;
- direction heterogeneity with a sign reversal;
- auditor-capability heterogeneity across the fixed panel;
- 5% technical missingness and 1-point differential missingness;
- lower baseline gate accuracy;
- higher clean false-block baseline; and
- the N=180 versions of any N=150 scenario that fails.

For every scenario report superiority power, clean non-inferiority power,
conjunctive power, superiority-null type-I error, non-inferiority-boundary
type-I error, bias, 95% coverage, interval width, and S1/S0 precision.  A
normal task-level interval is allowed only for design iteration; before freeze,
its operating characteristics must be calibrated on at least 1,000 simulated
datasets against the exact bootstrap-t implementation used by the locked
analysis.

Power is a design gate, not spending authorisation.  The study remains blocked
unless the powered design fits independently frozen money, token, wall-clock,
human-hour, privacy, and provider-failure limits.
