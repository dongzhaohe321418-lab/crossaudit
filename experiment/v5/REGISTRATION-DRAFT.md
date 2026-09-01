# CrossAudit v5 confirmatory study — prospective registration draft

**Status:** DESIGN DRAFT; NOT FROZEN; NOT DISPATCHED

**Predecessor:** the sealed v4 six-task cohort is feasibility evidence only and
will not enter a v5 effect estimate or power prior.

## 1. Primary question and claim boundary

The primary question is whether cross-vendor audit assignment, averaged over a
prospectively fixed panel of included configurations, improves controller gate
correctness relative to the matched-vendor/same-snapshot reference while
remaining non-inferior on clean-artifact burden.

The headline is conjunctive:

1. the lower bound of the two-sided 95% interval for the included-vendor
   standardised `correct_gate` risk difference is greater than zero; and
2. the upper bound of the one-sided 95% interval for the clean unnecessary
   escalation risk difference is below +0.05.

The claim is limited to the included tasks, domains, model snapshots, providers,
and controller.  No vendor-population or future-model claim is allowed.  A
directionally heterogeneous, null, or adverse result is a valid outcome.

## 2. Assignment factors

The study separates three comparisons that v4 could not identify:

- **S0 matched model:** generator and auditor use the same pinned snapshot;
- **S1 same vendor, different model:** the auditor is a distinct pinned model
  from the generator's vendor; and
- **S2 cross vendor:** the auditor is a pinned model from either of the other
  two included vendors.

The primary 3 x 3 matrix uses one principal snapshot per vendor, with every
principal model serving as Generator and Auditor.  S1 adds one alternate auditor
snapshot per vendor.  All prompts, tool access, temperature, maximum tokens,
context construction, and controller logic are fixed across applicable cells.

## 3. Tasks and artefacts

The initial sample is 150 independent task briefs, blocked equally over three
domains.  At least 60 are privacy-approved real-task or repository replays;
replays are shadow-only and cannot write to the original repositories.

Each task supplies, where applicable:

1. one natural principal-generator output;
2. one verified-clean controlled artefact; and
3. one exactly-one-mutant sibling derived from the same base artefact.

Mutation class, detection channel, task source, domain, natural/controlled
status, and clean/defective status are frozen balancing variables.  Unusual but
correct hard negatives are included among verified-clean controls.  No output
from the six-task v4 convenience corpus is eligible.

Each required artefact x auditor x Constitution cell receives three independent
fresh-context audit repeats.  The task, not the call, finding, defect, or repeat,
is the independent unit.

## 4. Human reference standard

Gold Panels enumerate defects before seeing model findings.  Matching Panels
map findings to frozen defects without seeing assignment labels.  Each item has
two independent domain reviewers; disagreement is resolved by a third reviewer.
Panel membership, training examples, adjudication rules, and calibration data
are hash-locked before dispatch.

Dispatch pauses unless an outcome-independent 30-item calibration reaches both
Krippendorff's alpha >= 0.80 and raw agreement >= 0.85.  Failure triggers rule
clarification and a new independent calibration set, not removal of difficult
study items.

## 5. Modules and call ceiling

| Module | Planned maximum calls |
|---|---:|
| Principal generation | 450 |
| Primary C2/D2 3 x 3 audit matrix | 12,150 |
| Same-vendor/different-model baseline | 4,050 |
| C0/C1 additions on a 60-task controlled subset | 6,480 |
| Paired 60-task whole-loop subset | 1,800 |
| **Total before authorised technical retries** | **24,930** |

Defensive-production and human ledger-utility studies are secondary appendices
unless separately powered and frozen.  They cannot rescue a failed primary.

## 6. Primary and key secondary outcomes

Primary outcomes are task-standardised `correct_gate` and clean unnecessary
escalation (effective false block, invalid response, or unresolved technical
failure).  Key secondary outcomes are defect recall, finding precision,
findings per artefact, repeat flip rate, final acceptability, resolved initial
defects, revision-introduced defects, unnecessary changes, human minutes,
model calls, tokens, latency, and monetary cost.

All assignment directions, S1 versus S0, review-only and DCL-negative strata,
and leave-one-vendor-out estimates are mandatory reports.

## 7. Mechanism ablations

The Constitution subset runs C0, C1, and C2 with three repeats in every cell.
The v4 repeat-0 feasibility diagnostic is not an effect estimate and is not
reanalysed into this cohort.  D0 model-only, D1 deterministic-only, and D2
combined-blind use the same underlying model and deterministic outputs; D1 is
not allowed to define its own gold labels.

## 8. Blinding, missingness, and stopping

Auditors do not receive origin, vendor, transcript, defect count, or mutation
labels.  Vendor codes remain opaque to analysts until the primary lock.
Provider identity must be resolved from provider-returned metadata or attested
deployment records; requested aliases alone are insufficient.

Every assigned call remains in the service-level intention-to-audit population.
Invalid or failed calls are incorrect gates and clean unnecessary escalations.
Complete-case and inverse-probability-weighted analyses are sensitivities only.

The global stop fires for any identity drift, arm leakage, hash drift, outcome
access before the primary lock, or safety-relevant provider event.  Operational
missingness stops are frozen by vendor before dispatch.  No failed direction or
model may be dropped after outcomes exist.

## 9. Go/no-go gates

- **G0 claim:** included-configurations wording is frozen.
- **G1 identity/design:** three vendors, six resolved snapshots, complete cells,
  task frame, and equal C0/C1/C2 repeats are verified.
- **G2 power:** at least 10,000 datasets per frozen scenario; central
  conjunctive power >= 0.80; superiority and non-inferiority boundary type-I
  error in [0.015, 0.035] and [0.04, 0.06], respectively (the positive
  superiority claim uses the lower end of a two-sided 95% interval); 95%
  coverage in [0.93, 0.97].  If N=150 fails,
  increase prospectively to 180; if N=180 fails, do not dispatch as an efficacy
  study.
- **G3 human:** the independent calibration gate in Section 4 passes.
- **G4 dry run:** a new outcome-blind 12-task operational cohort is excluded
  from inference, has >=98% valid calls, <=1 percentage-point differential
  missingness, and no identity/blinding/hash drift.
- **G5 freeze:** prompts, tasks, power output, analysis code, table shells,
  panels, randomisation, costs, privacy approvals, and stopping rules are
  hash-locked and externally timestamped.
- **G6 reporting:** superiority and non-inferiority must both pass, with no
  unexplained severe directional reversal, before any positive efficacy claim.
