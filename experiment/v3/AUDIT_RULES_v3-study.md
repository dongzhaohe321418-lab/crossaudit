# Constitution, scoped to the v3 synthetic corpus

**Status.** Proposed 2026-08-04. Not in force until the operator enacts it as a
dated amendment to `experiment/v3-ABLATION-REGISTRATION.md`. The loop may
propose rules; only the principal enacts them.

## Why a scoped rulebook, and what scoping costs

Three rounds of live smoke testing established that the study's synthetic
corpus cannot satisfy the deployment Constitution, and that this is not a
corpus defect to be patched away. Some rules ask for things a template
generator cannot produce: a real molecular geometry, an optimisation history,
a judgement about community norms. An auditor applying those rules to this
corpus reports findings on every clean increment, correctly, and the
false-block rate then measures the corpus rather than the auditor.

A rule the corpus cannot satisfy is not decidable against that corpus, and
decidability is what the protocol asks of every rule. Scoping is therefore not
a concession; it is the criterion applied honestly. What it costs is
generality, and the cost is stated here rather than discovered by a reader:
**results under this rulebook say nothing about how these arms would behave
against a rulebook that asks for chemistry.** That is the study's boundary and
it belongs beside every number.

v1 ran under an implicit version of this scoping and did not say so. Saying it
is the improvement.

## In force for this study

| Rule | Kept because |
|---|---|
| `CA-DATA-001` | Units and provenance are fields; a generator can write them and an auditor can check them. |
| `CA-DATA-002` | Internal contradiction is checkable from committed artefacts alone. |
| `CA-DATA-003` | Exclusion claims live in metadata and prose, both of which the corpus writes. |
| `CA-METH-002` | Convergence is stated in the record and evidenced in the log, so the claim and its evidence are both present. |
| `CA-REPRO-001` | Self-description is a list of fields, all of which the corpus ships. |
| `CA-REPRO-002` | The rerun path is a string that either resolves against shipped files or does not. |
| `CA-META-001` | Missing evidence is a finding, and it applies to any corpus. |
| `CA-META-002` | Report validity is a property of the report, not of the science. |

## Out of scope, and why

| Rule | Why it cannot be decided against this corpus |
|---|---|
| `CA-METH-001` | Asks whether the executed method matches the declared one. The corpus has no execution; the log is generated, not run. |
| `CA-METH-003` | Asks whether parameters sit within community norms. That is the judgement `CA-META-003` tells the Auditor not to legislate, and the corpus's parameters are drawn at random from plausible lists rather than chosen. |
| `CA-DOM-001` | Comparability across theory levels needs real energies at real levels. |
| `CA-DOM-002` | Geometry provenance needs a geometry with a history. The corpus ships placeholder atoms, which is exactly what an auditor reported. |
| `CA-META-003` | A constraint on the Auditor's behaviour rather than a rule to apply. It stays in the system prompt and is not scored. |
| `CA-META-004` | Escalation on a competence boundary is a verdict, not a finding, and this study scores findings. |

Six of fourteen out. The seeded defect classes were checked against this
subset before scoping: every class in the key is decidable under a rule that
remains, so nothing in the study's ground truth depends on a rule that left.

## One addition, from a measured failure

**`CA-NUM-001` — Arithmetic belongs to the deterministic channel.**
*Severity:* ADVISORY. *Criterion:* a finding that two numbers disagree must
state a tolerance, and that tolerance must be at least the printed precision of
both numbers. Where establishing the disagreement takes arithmetic — a unit
conversion, a sum, a ratio — the Auditor marks the pair as requiring tool
verification instead of raising a BLOCKER on a calculation of its own.

This rule was drafted once and rewritten once, and the rewrite is the more
interesting half.

The first version required the Auditor to convert units before comparing and to
state its tolerance, because the smoke runs had produced auditors that compared
eV against hartree without converting, and read `4.072310e-07` against
`4.07231e-07` as a discrepancy. That version worked, in the narrow sense that
auditors began showing the conversion.

Then the conversions were checked. Across five clean increments the Auditor
quoted the right constant, read the right inputs, and got the product wrong by
up to 1.8e-3 eV — while adjudicating whether a record and its log differed by
8.8e-5 eV. The error it introduced was twenty times the discrepancy it was
weighing, and its verdicts followed it exactly: the two increments it called
contradictory were the two where its multiplication was worst, and the three it
cleared were the three where it happened to multiply well. Every one of those
five records agreed with its own log to inside the precision both were printed
at, which a four-line script establishes without ceremony.

So the defect was never omission, and a rule demanding better disclosure could
not reach it. Numeric agreement across units is decidable, and I4 says a
decidable question is not a model's to answer. The Auditor's job on such a pair
is to notice that it exists and route it, not to settle it.

The rule stays ADVISORY. It constrains how a finding is expressed, not what the
science must be, and promoting a rule about the Auditor's own reasoning to
BLOCKER would let the loop argue about argument.

**Reply contract (not a rule).** The same run exposed a defect in the harness
rather than the rulebook: with `findings` the only place to write, an auditor
asked to show its working wrote the working there, and filed nine verdicts of
compliance — "these match exactly", "no finding under CA-DATA-002" — as
findings. `run_rung.py` now offers `checks_performed` on every rung, worded
identically on all of them, so the ladder keeps measuring isolation rather than
prompt hygiene.

## Effect on the study's claims

Recall and false-block rates under this rulebook are rates against eight
rules, on template-generated data, with numeric comparisons required to state
a tolerance. Reported that way, they answer the registered question about
isolation, and they answer nothing about domain competence. The write-up says
so in the same sentence as the numbers.
