# CrossAudit v4 execution-feasibility results

**Run date:** 2026-09-01
**Claim boundary:** execution feasibility; non-confirmatory; no vendor-population
claim
**Confirmatory v4 status:** `NOT RUN`

This report records the model-only, six-task feasibility evidence for all seven
v4 design questions. It does not complete the registered 120-task study, its
human Gold and Matching Panels, or its confirmatory inference. Task endpoints
below use descriptive task-cluster bootstrap intervals over at most six
deterministic convenience tasks; ledger endpoints instead cluster over the
seven fixed episodes.

## Evidence chain and the two cohorts

The two cohorts are separate and are **not pooled**.

| Cohort | Purpose | Scheduled / invoked | Valid | Other ITT statuses | Known cost |
|---|---|---:|---:|---|---:|
| Amendment 1 | Fail-closed infrastructure diagnosis | 472 / 37 | 36 | 1 provider-event policy violation; 435 safety-stop blocked | USD 1.1381591 |
| Amendment 2 | Primary feasibility cohort | 542 / 542 | 542 | none | USD 12.1504115 |

Amendment 1 correctly stopped after an OpenAI CLI WebSocket TLS-handshake
failure appeared in an error event. Its 36 valid observations are not a
scientific effect sample. They are retained as evidence that the global safety
stop worked, and they are never combined with Amendment 2.

Amendment 2 was registered after that failure and changed only the treatment of
one byte-exact, content-free transport-startup failure. Every other error,
action, malformed event, identity drift, or possible secret remains fail-closed.
The post-amendment canary passed before a new freeze. The outcome-free journal
was then sealed and pushed before scoring:

- freeze commit: `59bf55b`; freeze digest
  `d4102a553395dad82b5e4147cb8a5e1e3f22d1fa2eea37b584a522bd8668830c`;
- pre-analysis seal commit: `64bf673`; seal digest
  `6f5a7e262995bfb8232544328f17d999d7ac9dbb12a30d8256abcd6ff200ba3a`;
- analysis commit: `8d8dd18`; receipt digest
  `cf45634fd3382079d52fe80d8aa93408b274aa69eb67c14b244ff418a105ccb5`.

The exact [seal](feasibility/results/2026-09-01-six-task-amendment-2/COHORT-SEAL.json),
[analysis receipt](feasibility/results/2026-09-01-six-task-amendment-2/ANALYSIS-RECEIPT.json),
and [machine-readable summary](feasibility/results/2026-09-01-six-task-amendment-2/summary.json)
are committed beside the append-only journal. Structural and semantic
completion passed: 542 calls were scheduled and completed, all 542 were valid,
the journal hash chain and frozen-core hash validated, and all expected module
cells were present. Anthropic supplied 270 invocations with verified identity
metadata. OpenAI supplied 272 invocations through the pinned alias, but its CLI
did not expose an authoritative resolved model identity, so those identities
remain explicitly unverified. There were no unknown-cost calls or safety
events.

## Results by the seven registered questions

### 1. Generator x auditor factorial

Both pinned configurations generated all six tasks and both auditors reviewed
both generators' natural, clean, seeded, and unusual-but-correct artefacts. In
the D0 model-only controlled endpoint, the fixed-weight correct-gate rates for
Anthropic-to-Anthropic, Anthropic-to-OpenAI, OpenAI-to-Anthropic, and
OpenAI-to-OpenAI were respectively 77.8%, 96.3%, 90.7%, and 94.4%. The
task-equal cross-minus-same contrast was +7.4 percentage points (descriptive
95% bootstrap interval +0.9 to +13.9). The corresponding clean/ambiguous
false-block rates were 33.3%, 5.6%, 13.9%, and 8.3%; cross-minus-same was
-11.1 points (-20.8 to -1.4).

The pooled-looking contrast masks direction heterogeneity. For
Anthropic-authored artefacts, OpenAI-auditor minus Anthropic-auditor was +18.5
points; for OpenAI-authored artefacts, Anthropic-auditor minus OpenAI-auditor
was -3.7 points. This is why both directions are retained rather than treated
as one universally beneficial `cross` condition.

These numbers show that the crossed measurement is executable and that the
direction of pairing can matter in this micro-corpus. They do not identify a
vendor effect: there are only two pinned configurations, six authored tasks,
and no human gold standard. The four-cell values, rather than a pooled
cross-vendor headline alone, remain the primary descriptive record.

### 2. DCL and Constitution ablations

On the same audit replies and artefacts, combined-blind D2 improved correct-gate
accuracy over model-only D0 by 18.75 points (14.58 to 22.92), with a 0-point
change in false blocks and escalation. The deterministic-only D1 checker scored
100% in each artefact type; this is a harness ceiling check because the same
checker defines the micro-task gold labels, not an unbiased estimate of DCL
performance. Relative to D1, D2 lost 7.64 points of correct-gate accuracy and
added 14.17 points of false blocks, illustrating that an LLM channel can add
burden even when the deterministic result is available. Among 288 C2/D0 audit
rows, 66 gold-defect catches were DCL-only and 72 were overlapping; 30
false-positive locations were LLM-only.

The +18.75-point D2-minus-D0 result came entirely from the natural stratum:
its four-cell mean rose from 25% to 100%, while the fixed-weight clean,
seeded, and ambiguous controlled endpoint did not change. The natural outputs
are exactly where the shared deterministic checker is most consequential, so
this result cannot be presented as an independent DCL efficacy estimate.

The prospective C0/C1/C2 subset contained only `F-DATA-01` and `F-SCI-01`.
The machine summary reports a zero C1-minus-C0 contrast, a -12.5-point
C2-minus-C0 correct-gate contrast (-25 to 0), and a +25-point false-block
contrast (0 to 50). However, the feasibility scorer restricts this comparison
to `repeat == 0`, whereas the registration states that C2 uses the three core
repeats. Those outputs are therefore retained only as repeat-0 implementation
diagnostics. They are excluded from the figure below and must not be described
as registered three-repeat Constitution effects. The discrepancy must be
resolved prospectively before a Constitution-effect analysis is interpreted.

[![Figure 5: configuration and component effects](../../paper/figures/figure5-v4-configuration-effects.png)](../../paper/figures/figure5-v4-configuration-effects.pdf)

**Figure 5 | Configuration- and component-specific feasibility effects.**
Panels a and b preserve the four C2/D0 Generator–Auditor directions and their
task-clustered pairing contrasts. Panels c and d isolate the DCL comparisons
and show that the D2-minus-D0 gain is confined to natural outputs; the three
controlled strata do not change. Error bars are descriptive 95% whole-task
bootstrap intervals over six deterministic convenience tasks. D1 is a harness
ceiling because the same checker defines the micro-task gold. Constitution
contrasts are intentionally absent because of the repeat-0 versus registered
three-repeat inconsistency above. [Vector figure](../../paper/figures/figure5-v4-configuration-effects.svg)
and [source data](figures/source-data.csv) are available alongside the PDF.

### 3. Defensive production and Goodhart proxies

For research-text outputs there were 12 sessions per policy arm. Initial
objective correctness was 25% in P0, P1, and P2: merely disclosing a shadow or
hard audit did not improve the first answer. P1 and P2 were shorter than P0 by
9.5 and 8.4 words on average, while P2 added 0.25 observable checks; neither
policy added measured disclaimers. Under the bounded hard-gate loop, P2 made
1.33 revisions per session and repaired 2 of 9 initially wrong sessions, taking
final correctness to 41.7% without regressing any of the three initially
correct sessions. That used 56 calls and USD 1.3081, versus 24 calls and USD
0.5313 for P0. P1 remained at 25% with 24 calls and USD 0.5896.
Among the 12 P2 delivered outputs, the deterministic P0-relative proxy labelled
two as functional improvements and two as compliance-only; the other eight were
neutral. The measured correctness gain is therefore inseparable from both
extra audit/revision compute and rule-surface adaptation in this design.

For scientific Python there were four sessions per arm. All arms were 100%
correct on visible and held-out fixtures and static validation, all averaged
2.5 LOC, and P1/P2 added zero wrappers, assertions, or exception/retry
constructs relative to P0. Observable checks rose from 3.75 per P0 output to
4.25 in both P1 and P2, but correctness was already at a 100% ceiling and no
code revision was needed. The frozen P0-relative labeler consequently called
three of four P1 outputs and three of four P2 outputs `compliance_only`; that is
a mechanically related deterministic surface proxy, not human semantic
adjudication.

The defensible conclusion is therefore narrow: this cohort did **not** show
general code bloat, defensive wrappers, held-out overfitting, or a correctness
penalty. It did show that a hard gate can consume substantially more calls and
can produce compliance-shaped differences, while a bounded loop sometimes
repairs an initially wrong answer. This is not evidence that agents generally
adopt defensive programming.

### 4. Controlled, natural, clean, and ambiguous evidence

The cohort retained 12 artefacts in each of four construction strata: unmodified
natural outputs, deterministic clean repairs, single seeded mutations, and
unusual-but-correct ambiguous controls. It did not silently pool them. All 48
artefacts had deterministic micro-task labels; the resulting set contained 27
clean and 21 defective labels.

This executes the controlled/negative-control measurement path but does not
satisfy the registered real-evidence requirement. There are no 60 real task
briefs, privacy-reviewed replays, human Gold/Matching Panels, two-reviewer
adjudication, or reliability intervals. Natural-output performance here is an
available-checker result on authored micro-tasks, not natural defect recall in
the intended scientific population.

### 5. Whole-loop net outcomes

All 24 seeded branches completed, 12 same-configuration and 12
cross-configuration. Both assignments resolved the initial seeded defect in
100% of branches, but final acceptability was 91.7% because the deterministic
proxy labelled a new defect in 8.3% and an unnecessary change in 25.0% of
branches. Both assignments averaged 1.083 revisions and 2.167 incremental
calls. Cross-minus-same was zero for resolution, final acceptability, new
defects, unnecessary changes, revision count, and call count. Mean incremental
known cost was USD 0.04574 cross and USD 0.04776 same; the task-clustered
difference was -USD 0.00202 (-0.00451 to +0.00003).

This is direct evidence that a `changed` field is not enough to call a repair
safe: regression and unnecessary-change checks must remain part of admission.
The labels are still deterministic micro-task proxies, and no human review
minutes or blind semantic judgements were collected.

### 6. Ledger utility

Seven episodes (one untampered and six distinct tamper challenges) produced 42
schema-valid proxy reviews: 14 for each interface E0 final-only, E1 transcript,
and E2 structured ledger. Correct accept/reject accuracy was 21.4% for E0 and
71.4% for both E1 and E2, so each richer surface improved the episode-equal
proxy contrast by 50.0 points (14.3 to 85.7). Tamper classification was 14.3%
for E0 and 71.4% for E1/E2, a +57.1-point contrast (14.3 to 85.7). E1 recovered
the origin and first defective round at 100% and 92.9%; E2 reached 92.9% and
57.1% respectively.

E2 did not improve the primary proxy endpoints over the ordinary transcript
E1: accept and tamper contrasts were both zero. First-defective-round accuracy
was lower for E2 than E1 by 35.7 points (-64.3 to -14.3). The feasibility
signal is therefore that exposing history helps relative to final-only, not
that the structured ledger surface has already beaten an ordinary log.

Raw provider latency averaged 11.36 seconds for E0, 18.38 for E1, and 15.24
for E2. The separate capped decision proxy, which assigns 300 seconds to an
incorrect or insufficient answer, averaged 238.60, 98.50, and 96.01 seconds.
That proxy is not human review time. Each attack appears in only one episode,
attack and episode are confounded, and the reviewers are fresh model sessions
rather than randomised humans. The result supports the feasibility of testing
ledger interfaces; it does not establish human ledger utility.

### 7. Repetition, integrity, inference, and stopping

All 96 C2 artefact-auditor cells had three valid fresh-context verdicts. The
verdict-flip rate was 5.21%. The study used an append-only, hash-chained journal,
zero retries, frozen cost/provider/elapsed/call caps, ITT failure states, an
outcome-free seal pushed before scoring, and a hash-bound analysis receipt.
Task-clustered descriptive contrasts required complete prospective cells and
listed incomplete clusters rather than silently reweighting them. The run
stopped only after the frozen schedule completed; it did not use efficacy or
futility peeking.

This verifies the feasibility integrity path, not the registered confirmatory
one. The 120/180-task power design, opaque arm custody through
`PRIMARY-LOCK.json`, human panel reliability, registered mixed-model/IPW
sensitivities, and blinded nuisance-only sample-size procedure remain unrun.

[![Figure 6: operational trade-offs](../../paper/figures/figure6-v4-operational-tradeoffs.png)](../../paper/figures/figure6-v4-operational-tradeoffs.pdf)

**Figure 6 | Operational gains, costs, and unresolved boundaries.** Panel a
shows the bounded P2 repair gain for research-text sessions; panel b shows its
additional calls, cost, and provider time. Panel c keeps repair, final
acceptability, new-defect, and unnecessary-change outcomes distinct despite
matching same- and cross-auditor rates. Panel d shows that both richer history
surfaces improve on final-only review, while the structured ledger does not
outperform the ordinary log on the primary proxy decisions. These are
configuration-specific feasibility measurements: the policy and whole-loop
endpoints cluster over at most six tasks, ledger endpoints over seven fixed
episodes, and proxy reviewers are not human participants. [Vector figure](../../paper/figures/figure6-v4-operational-tradeoffs.svg)
and [source data](figures/source-data.csv) are available alongside the PDF.

## Completion classification

| Point | Six-task feasibility | Registered confirmatory study |
|---|---|---|
| 1. Generator x auditor factorial | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 2. DCL and Constitution ablations | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 3. Defensive production | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 4. Evidence mixture | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 5. Whole-loop net outcome | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 6. Ledger utility | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |
| 7. Repetition, integrity, inference, stopping | `EXPLORATORY` | `INCOMPLETE / NOT RUN` |

All seven proposed modules were implemented and executed with real provider
calls at feasibility scale. None is labelled `COMPLETE`, because that term is
reserved by the prospective acceptance contract for the registered human-
adjudicated study. Reporting this distinction is part of completing the work,
not a reason to erase the data that now exist.
