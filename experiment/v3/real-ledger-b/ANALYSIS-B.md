# Second-snapshot analysis of the live deployment ledger

**Freeze.** science `485106fa144ccd74fff77144634b65e15c38eb71`, audit
`abb10a4781d954a66412201f103246852f1540f3`, taken 2026-08-03. Regenerate with
`python3 experiment/v3/analyse_ledger.py <science> <audit> <out>`; the script
is part of the freeze. Both repositories are read-only inputs. Everything below
is process metadata — cycle identities, decisions, severities, the deployment's
own source labels, rule citations, timestamps. No scientific content was read,
quoted, or judged, and none of these numbers is a statement about the chemistry.

**Standing.** The v3 registration's Part B labels remain frozen at the 31 July
snapshot (7 cycles, 14 findings, 12 confirmed). Nothing here amends them. This
is a later, larger observational snapshot reported as operational telemetry.

## What the snapshot contains

21 model-audited cycles, 39 findings, 23 distinct finding IDs, 20 behaviourally
confirmed closed, 3 open at the freeze. Auditor models `gpt-5`, `gpt-5.6`,
`gpt-5.6-sol`. Decisions: 15 BLOCK, 3 PASS\_WITH\_CAVEATS, 3 PASS.

## 1. A retraction, first

In the previous session's proposal I suggested that the deployment's auditor
"passes the discrimination test the synthetic cross-vendor arm failed", on the
grounds that it issues PASS as well as BLOCK, and that its verdicts agree with
its findings. **Checking it properly kills it, and I withdraw it.**

The decision is fully derivable from the findings' `blocked_scopes`, with no
exceptions in 21 cycles:

| Decision | Any blocking finding present | Cycles |
|---|---|---|
| BLOCK | yes | 15 |
| PASS\_WITH\_CAVEATS | no | 3 |
| PASS | no (zero findings) | 3 |

Verdict-versus-findings agreement is therefore **definitional, not evidential**.
It tells us the verdict synthesiser is consistent, which is worth knowing about
the implementation and worth nothing as evidence about the auditor's judgement.
The synthetic trial's constant-verdict problem was that a stub reproducing the
verdict distribution would score identically; this snapshot cannot rebut that
concern, because the ledger records no independent ground truth about which
increments deserved to be blocked. What would rebut it is Part B's blinded
adjudication, which remains unrun.

## 2. There are two regimes, and only one of them is in the paper

| Phase | Cycles | Findings per cycle | Mean |
|---|---|---|---|
| Initial cleanup | 1–9 | 7, 4, 3, 2, 1, 1, 0, 0 | 2.25 |
| Sustained development | 10–22 | 1, 1, 1, 1, 0, 1, 1, 3, 3, 1, 3, 2, 3 | 1.62 |

The paper reports the first arc, where findings fall to zero and the loop
converges. The second phase does not converge to zero; it settles at roughly one
to three findings per cycle and stays there. **The steady state, not the
convergence, is what a long-running deployment actually experiences**, and it is
the regime the paper's cost argument needs.

Two cautions on this comparison, both disqualifying for any causal reading. The
phases are not matched: the first audited an accumulated backlog, the second
audits fresh increments, so the workloads differ in kind. And the boundary was
chosen after seeing the series, which is exactly the freedom that makes
post-hoc segmentation untrustworthy. The honest statement is descriptive: the
finding rate did not stay at zero once development resumed.

## 3. Cadence

Audit duration: median 6.0 minutes (range 3.7–18.2). Interval from one audit
finishing to the next starting: median 34 minutes, quartiles 18 and 70, maximum
2910 (an overnight gap). Wall-clock is therefore dominated by the repair side,
not the audit side. This bears on the paper's cost claim only weakly: it shows
the audit is not the bottleneck, and says nothing about how much human attention
the repairs consumed, which is the quantity the claim is actually about and
which the ledger does not record.

## 4. What caught the defects, by the deployment's own label

Each finding carries a `source` field written by the auditor.

| Source | Findings | Severity spread |
|---|---|---|
| JUDGMENT | 28 | 24 HIGH, 3 MEDIUM, 1 CRITICAL |
| DETERMINISTIC | 11 | 6 LOW, 2 HIGH, 2 CRITICAL, 1 MEDIUM |

Read carefully, this answers "what did catch it", not "what could have caught
it". Those are different questions, and only the second is the mechanisability
endpoint the registration defines. A JUDGMENT finding may well have been
catchable by a check nobody had written. So the honest reading is: **at least
11 of 39 findings were mechanical; how many more of the 28 could have been is
undetermined and needs the principal's per-finding adjudication.** The severity
spread is suggestive in the other direction, though — the deterministic layer
produced both CRITICAL findings and most LOW ones, while judgement produced
almost all the HIGH ones — and it should not be over-read either, since severity
is assigned by the same auditor.

## 5. Rule concentration

Twelve distinct rules were cited across the 21 cycles. The distribution is
extremely uneven:

| Rule | Findings citing it | Distinct cycles it fired in (of 21) |
|---|---|---|
| Gate 11 | 25 | 16 |
| R-STA-002 | 13 | 12 |
| Gate 2 | 8 | 6 |
| R-EVD-002 | 7 | 6 |
| R-GRD-001 | 4 | 4 |
| R-EVD-006 | 3 | 3 |

One rule fires in three quarters of all cycles. This is the hit-rate telemetry
the paper's standards-ratchet argument asks for and has never had. It does not
by itself say whether the rule is load-bearing or too broad; that needs the
rule text, which is the principal's to read. What it does establish is that
**rule usage in a real deployment is heavy-tailed**, so a ratchet that promotes
or tightens rules on hit rate will be dominated by a handful of them.

Caveat on extraction: rule identifiers are parsed from the findings' evidence
strings by pattern match. Two forms appear (`R-XXX-000` and `Gate N`) and the
counts are of citations, not of distinct violations.

## 6. Closure lag and recurrence

Median 1 cycle from first raise to verified closure; mean 2.10; maximum 7. Ten
of the 23 distinct findings appear in more than one cycle, F-019 in five.
Repeat appearance is the measurable form of "fixed, but not fixed properly", and
it is the signal a re-audit is for. It is also, in part, a consequence of how
this deployment batches: a finding stays listed while its repair commit is not
yet contained in the audited snapshot, which is a bookkeeping state rather than
an unresolved defect. Distinguishing the two requires reading the reports, which
is the principal's call.

## 7. Scope-granular blocking

`publish_claim` was blocked by 33 findings, `submit_production_job` by 12. The
deployment's four-level severity ladder maps onto two gated scopes rather than
onto a single pipeline halt, which is the divergence from the protocol's
two-level scheme that §4.2 of the paper names. The distribution shows the finer
gate being used, not merely available.

## What this snapshot cannot support

It is one deployment, one operator, one domain, 21 cycles. There is no control
condition, no blinding, and no independent ground truth about which increments
deserved blocking. Every rate here is descriptive. In particular it cannot
show that cross-vendor audit outperforms same-vendor audit, cannot establish a
false-positive rate, and cannot settle the mechanisability question it partially
illuminates.
