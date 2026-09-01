# CrossAudit v4 Causal Successor Study — Registration

**Registered:** 2026-09-01
**Status:** registered successor study; not yet run
**Authority:** this document, together with `SAP.md`, `POWER.md`,
`STOPPING-RULES.md`, and the hash manifest that must be created before dispatch,
is the prospective authority for v4.
**Prior-study boundary:** v1–v3 remain frozen historical studies. Nothing in
this directory amends, rescues, re-scores, or replaces their registrations or
results.

At registration, no v4 model-arm output existed and no v4 outcome had been
inspected. Model identities, the randomisation seed commitment, the external
ground-truth commitment, and the monetary/call budget cap are deliberately
unfilled blocking fields in `config/study.yaml` and `config/models.lock.json`.
They must be frozen and hash-bound before any confirmatory call. A missing field
prevents dispatch; it is not permission for an operator to choose it after
seeing results.

## 1. Purpose and registered questions

The v1 pilot showed that two model configurations could read one rulebook very
differently, but it did not instantiate a generator–auditor vendor pairing and
had only one run per configuration. v3 registered an isolation ladder and
channel decomposition, but the ladder changes several things at once and its
model arms remain a separate, frozen programme. v4 is a new causal successor
designed to answer seven questions.

1. **Pairing:** for fixed, pinned model configurations, does assigning an
   auditor from a different vendor rather than the generator's vendor improve
   the probability of a correct admission decision?
2. **DCL and Constitution:** what are the causal contributions of the
   Deterministic Check Layer (DCL) and of increasingly decidable rulebooks?
3. **Defensive production:** does anticipation or enforcement of audit induce
   compliance-only output, conservative choices, disclaimers, or escalation
   without improving independent task quality?
4. **Data ecology:** do conclusions agree across controlled seeded defects,
   natural model defects, real-task replay, and verified clean negative
   controls?
5. **Whole loop:** after audit-guided revision, how many real defects are fixed,
   how many new defects are introduced, and how much work is unnecessary?
6. **Ledger value:** does a structured, hash-bound ledger improve an independent
   reviewer's accuracy, reconstruction time, and tamper detection relative to
   a final artefact or an ordinary transcript?
7. **Reliability and inference:** are effects stable across independent runs and
   defensible under blinded human adjudication, task-level clustering, a
   prospective power plan, and fixed stopping rules?

No single omnibus number answers all seven questions. Question 1 supplies the
confirmatory headline. Questions 2–7 have separately defined endpoints and
claim rules below and in `SAP.md`.

## 2. Confirmatory factorial core

### 2.1 Two-vendor minimum

The minimum confirmatory design is a complete generator-vendor × auditor-vendor
2×2. Vendor codes are blinded labels until the primary analysis is locked.

| Generator vendor | Auditor A | Auditor B |
|---|---|---|
| A | same-vendor | cross-vendor |
| B | cross-vendor | same-vendor |

For every task brief, both generators independently produce an artefact. Every
artefact is then audited by both auditor vendors in fresh contexts. Thus the
same artefact supplies a paired same-vendor and cross-vendor comparison; a
generator's output quality cannot explain the within-artefact contrast. Both
directions are mandatory. A one-direction study, such as A-generated work
reviewed only by B, is incomplete and cannot carry the registered claim.

Within each vendor's core cell, Generator and Auditor use the **same pinned
model snapshot** under role-specific, hash-matched generation/audit prompts and
fresh contexts. This instantiates same-model/same-vendor review rather than
silently substituting a same-vendor model of different capability. A
same-vendor-different-model arm may be registered as a secondary parametric-
separation contrast, but it cannot replace the core diagonal.

The confirmatory auditor condition uses the decidable Constitution (`C2`) and
the registered combined DCL policy (`D2`). DCL output is not disclosed to the
auditor in D2; the controller combines two independently generated signals.
This keeps the Question 1 contrast about auditor assignment rather than about
different context supplied to different vendors.

Each artefact × auditor-vendor cell is called **three times**, in independent
fresh contexts. A technical retry that sends byte-identical input after a
transport failure is not a repeat and is governed by `STOPPING-RULES.md`.

### 2.2 Exact estimand and claim rule

The primary outcome is `correct_gate`:

- an artefact with at least one independently validated BLOCKER should be
  blocked;
- a verified clean artefact, or one containing only advisory/out-of-scope
  material, should not be blocked;
- an invalid, empty, rule-free, or unparseable audit is an escalation and is
  incorrect for this endpoint under intention-to-audit.

The primary estimand is the marginal, task-population-standardised risk
difference

\[
\Delta_{cross}=
P(correct\ gate\mid cross)-P(correct\ gate\mid same),
\]

equally standardised over generator vendors, registered domains, controlled
clean/defective status, and audit repeats. The headline claim requires both:

1. superiority: the two-sided 95% confidence interval for
   \(\Delta_{cross}\) excludes zero in the beneficial direction; and
2. safety: cross-vendor clean false-blocking is non-inferior to same-vendor
   false-blocking, with the pre-registered upper margin of **+5 percentage
   points** under a one-sided 95% interval.

The second gate prevents a reviewer that blocks everything from succeeding by
recall alone. Failure to meet either condition is a null/qualified result, not a
reason to change the endpoint.

### 2.3 What two vendors can and cannot establish

With exactly two vendors, generator main effect, auditor main effect, and the
same/cross diagonal contrast saturate the four cell means. The estimate is a
causal comparison for the two pinned configurations on the registered task
population, but it is not a population-level vendor effect. A two-vendor result
must be written as:

> For these pinned generator and auditor configurations, tasks, prompts, and
> dates, cross-vendor assignment changed the outcome by …

It must not be written as “cross-vendor auditing generally works better”.

### 2.4 Three-or-more-vendor extension

An extension may add vendor C or more vendors only before that extension's own
freeze. It must complete the full V×V matrix: every vendor generates and every
vendor audits every generator's artefacts. Adding only a favourable cross arm
is prohibited.

- Two vendors: `claim_scope = pair_specific`.
- Three or more complete-matrix vendors: `claim_scope = included_vendors_only`;
  report vendor-pair heterogeneity and leave-one-vendor-out estimates.
- A claim about vendors as a population remains prohibited with three vendors.
  Such a claim requires a substantially broader vendor sample (the target is at
  least five independent vendors/model families) or a prospective meta-analysis
  across independent studies.

Results from an extension are a separately frozen cohort and do not retroactively
change the two-vendor primary analysis.

## 3. Tasks and data strata

### 3.1 Registered scale

The initial plan is **120 task briefs**, with a maximum of **180** only through
the blinded sample-size re-estimation in `POWER.md`. Task briefs are blocked
equally across at least three registered domains:

1. computational-science increments;
2. quantitative data analysis; and
3. scientific Python or analysis code.

The exact task list, domain allocation, input manifests, and licence/privacy
review must be frozen before generation. Tasks cannot be selected or removed
using arm outcomes.

### 3.2 Controlled seeded stratum

Each task brief is independently completed by each generator vendor. Candidate
base artefacts are checked without auditor outputs. An eligible controlled base
must pass the named DCL and domain tools and be independently confirmed clean
by the Gold Panel. Ineligible bases are retained in the natural-defect stratum;
they are not silently repaired and called clean.

Each eligible base yields two opaque artefacts:

- one verified clean negative control; and
- one defective variant containing exactly one target mutation.

Each mutation has a unique `defect_id`, exact location, blocking status,
rule-coverage label, and cheapest expected catching channel. The target classes
are balanced over:

- generic DCL-visible defects;
- domain-tool-visible defects;
- Constitution-decidable semantic defects;
- review-only semantic defects that survive the frozen deterministic layer;
- out-of-scope or unusual-but-correct cases, which must not block.

Clean/mutant siblings receive unrelated opaque IDs and are separated in audit
order. The defect key and mapping are encrypted or externally escrowed before
any auditor call; a hash-only public commitment is not sufficient for a
blinding claim.

### 3.3 Natural-defect stratum

At least 60 registered real task briefs, balanced by domain and generator
vendor, are completed without mutation. The Gold Panel enumerates defects from
the artefact and task specification before seeing any auditor output. This
stratum measures natural generator failures rather than mutator detectability.
It is a key secondary external-validity analysis and is not used to tune the
Constitutions or DCL.

### 3.4 Real-task replay

Real-task replay uses immutable, privacy-reviewed snapshots of task
specifications and inputs from authentic workflows. All work occurs in isolated
copies; no live science repository is modified and no generated result is
admitted downstream. Each replay task is sent to every registered generator
vendor, and the complete auditor matrix is run in shadow mode.

Historical behavioural closure (“a later commit says it fixed F-001”) may be
reported as provenance but is not ground truth. Compliance with a finding is
endogenous and cannot prove that the finding was correct.

### 3.5 Verified clean controls

Clean controls must include both ordinary cases and unusual-but-correct hard
negatives. A clean label requires:

- all frozen applicable deterministic checks to pass;
- two Gold Panel members to independently find no blocking defect;
- any disagreement to be resolved by a third adjudicator before audit; and
- a locked artefact manifest and label commitment.

If a post-freeze genuine defect is discovered in a nominally clean artefact, it
is handled under the frozen relabelling and sensitivity procedure in `SAP.md`;
the artefact is never quietly deleted.

## 4. DCL and Constitution ablation

### 4.1 Constitution factor

The three registered levels are:

- `C0`: no substantive Constitution; output contract only;
- `C1`: broad, human-readable generic rules;
- `C2`: the same concepts expressed as scoped, decidable criteria.

`C1` and `C2` must use the same rule IDs, severity intentions, conceptual
coverage, order, and approximately matched token length. C2 may sharpen a
criterion but may not add a defect family that C1 never mentions. This makes
the C1→C2 contrast about decidability rather than coverage or prompt length.
The three files under `constitutions/` are templates until their scope and
hashes are frozen in the dispatch manifest.

Primary Constitution contrasts, Holm-corrected as one family, are:

1. C0 vs C1: contribution of an explicit rulebook;
2. C1 vs C2: contribution of decidability; and
3. C0 vs C2: total rulebook contribution.

### 4.2 DCL factor

- `D0 LLM_ONLY`: model audit alone determines the model-side gate.
- `D1 DCL_ONLY`: the frozen deterministic layer acts without an LLM.
- `D2 COMBINED_BLIND`: DCL and model run independently; the auditor does not
  see DCL output, and the controller applies deterministic precedence.
- `D3 ROUTED` is optional and exploratory: the auditor receives structured DCL
  pass/fail/referral output. It requires new model calls and never enters the
  Question 1 primary contrast.

D0, D1, and D2 should be reconstructed from one DCL run and one model reply
where possible, so their difference cannot be caused by stochastic reruns.
Report class-specific and workload-standardised effects because an overall DCL
effect is otherwise determined by the experimenter's chosen mix of mechanical
defects.

The confirmatory ablation tests D0 vs D2 and the C×D interaction. D1 quantifies
the non-model floor and the residual review-only stratum.

### 4.3 Allocation

The full C0/C1/C2 model-call ablation may run on a prospective, domain- and
stratum-balanced subset to control cost. The subset size and sampling seed are
blocking fields that must be power-justified and frozen before any ablation
output. Every included artefact is run under every Constitution level and every
auditor vendor, with three repeats. No subset may be chosen after inspecting
the C2 primary replies.

## 5. Blinding, randomisation, and adjudication

### 5.1 Auditor blinding

Before audit, a deterministic scrubber removes provider names, model IDs,
request IDs, conversation transcripts, and explicit generator-origin metadata.
It may not rewrite substantive content or normalise style. Auditors receive an
opaque artefact ID, task specification, artefact, assigned Constitution, and
the common reply schema. They are not told whether defects were seeded, how
many exist, or whether the artefact is a clean control.

### 5.2 Execution blinding

- Calls are randomised within blocks of task, generator vendor, domain, and
  data stratum.
- Every call uses a fresh context and identical tool permissions.
- No arm output is opened until the corresponding execution block is complete.
- The operator-facing mapping from opaque codes to vendors is sealed.
- Analysts receive blinded arm codes until code, exclusions, and primary tables
  are locked in `PRIMARY-LOCK.json`.

### 5.3 Human ground truth

Two independent human processes prevent incorporation bias.

1. **Gold Panel:** two domain-qualified reviewers inspect each natural/real
   artefact without seeing any model findings and enumerate all blocking and
   advisory defects. A third reviewer resolves disagreements.
2. **Matching Panel:** reviewers, blinded to all arm identities, match each
   anonymous model finding to at most one gold defect and label unmatched
   findings `valid_new`, `invalid`, or `unclear`. A valid new finding returns to
   the Gold Panel without source information.

The adjudication manual and calibration set are frozen before production
labels. Inter-rater reliability and its interval are reported. If the stopping
threshold in `STOPPING-RULES.md` is reached, the affected stratum is paused or
downgraded; arm identities are never revealed to improve agreement.

## 6. Whole-loop revision study

A prospectively sampled, domain/stratum/vendor-balanced set of defective and
natural artefacts enters a bounded two-round loop:

`initial artefact → audit → revision → re-audit → optional second revision`.

The sample size, sampling seed, audit condition, and whether same/cross is
assigned or crossed must be frozen before loop execution. Every revision is a
new content-addressed artefact; earlier versions are immutable.

Blinded reviewers record:

- initial validated defects;
- initial defects resolved;
- initial defects remaining;
- new defects introduced;
- findings that drove no necessary change;
- compliance-only, neutral, and harmful changes;
- final acceptability, calls, tokens, latency, and human escalation time.

Primary loop outcomes are the fraction of initial defects resolved and the
probability the final artefact is acceptable. New-defect rate and unnecessary-
change rate are co-reported safety outcomes. A composite “net correction” may
be descriptive only unless every weight is frozen before execution.

## 7. Defensive-production study

Fresh generator sessions are randomised to:

- `P0 UNAWARE`: no audit is mentioned;
- `P1 SHADOW_AWARE`: the generator is told an independent check will occur but
  that it cannot gate the result; and
- `P2 HARD_GATE`: the generator is told audit gates completion and receives
  findings under the bounded revision loop.

The same task blocks are used across policies, with independent sessions to
avoid carry-over. The exact disclosure text is frozen. The policy experiment
measures output volume, file count, metadata/disclaimer share, wrappers and
duplicate assertions, method novelty, escalation requests, final independent
task quality, held-out semantically equivalent checks, cost, and delay.

Blind change-level labels are:

`functional_improvement`, `necessary_evidence`, `compliance_only`,
`defensive_disclaimer`, `neutral`, and `harmful`.

The registered claim of defensive production requires increased compliance-
only or defensive content under P1/P2 without a commensurate improvement on
independent quality and held-out checks. Mere length increase is not enough.

## 8. Ledger-value study

Independent reviewers are randomised at episode level to one evidence surface:

- `E0 FINAL_ONLY`: final artefact only;
- `E1 TRANSCRIPT`: final artefact plus an ordinary chronological transcript;
- `E2 STRUCTURED_LEDGER`: final artefact plus the structured CrossAudit ledger.

No reviewer sees more than one surface for the same episode. Episode allocation
uses a balanced incomplete-block or Latin-square design over reviewers. Known
tamper challenges are seeded before allocation: stale receipt, wrong commit,
changed Constitution, missing round, altered report, and unsupported provider
identity claim. The attack key is blinded and externally committed.

Primary ledger outcomes are correct accept/reject judgement and time to a
correct decision. Secondary outcomes are identification of the first defective
commit, applicable rule version, tamper-detection rate by attack class, reviewer
confidence calibration, and review burden. This study evaluates the ledger;
auditor recall is not evidence of ledger value.

## 9. Endpoints

### 9.1 Primary

1. Standardised risk difference in `correct_gate`, cross minus same.
2. Clean false-block risk difference, evaluated against +5 percentage-point
   non-inferiority margin.

### 9.2 Key secondary

- validated BLOCKER-defect recall;
- clean specificity and false-block rate by vendor direction;
- finding precision/positive predictive value;
- review-only defect recall;
- DCL/tool/model exclusive and overlapping catches;
- out-of-scope overreach;
- unknown-rule citation and rule-grounding rates;
- malformed/empty/escalated reply rate;
- finding count and severity inflation;
- repeat-level verdict flip and finding overlap;
- token, monetary, latency, and human-attention cost;
- whole-loop repair, regression, and unnecessary-change outcomes;
- defensive-production and ledger outcomes defined above.

Raw recall, finding count, or BLOCK frequency is never a stand-alone quality
endpoint.

## 10. Statistical analysis and power authority

`SAP.md` freezes analysis populations, estimators, contrasts, multiplicity,
missingness, and sensitivity analyses. The principal estimator first collapses
repeats and artefacts within task, forms the balanced mean of the two cross
directions minus the balanced mean of the two same-vendor directions, and uses
whole-task bootstrap intervals. A logistic mixed model with the registered
fixed effects and task/base-artefact/model-panel clustering is a sensitivity
analysis, not the source of the headline estimate. The paper reports
standardised risk differences rather than interpreting an isolated log-odds
coefficient.

`POWER.md` defines a smallest effect of interest of eight percentage points,
the 120-task initial design, the 180-task hard maximum, three audit repeats,
simulation requirements, and the single blinded nuisance-parameter sample-size
re-estimation. Natural/real external validation does not rescue an underpowered
controlled primary analysis.

## 11. Missingness and protocol deviations

The primary population is intention-to-audit. Invalid model replies count as
escalations and incorrect gates unless the task truly requires escalation.
Transport failures receive at most two byte-identical technical retries. A
still-missing call remains missing, is never hand-filled, and enters pre-specified
worst-case and inverse-probability sensitivity analyses.

Every deviation is appended before reveal with time, actor, affected cells,
reason, and disposition. No deviation may silently redefine the endpoint,
corpus, matching rule, or analysis population.

## 12. Freeze and dispatch gates

Before the first confirmatory call, all of the following must exist and agree:

1. exact model/provider/API snapshot and capability lock;
2. exact task/corpus/input manifests and privacy approvals;
3. generator, auditor, scrubber, DCL, tool, rulebook, schema, matcher, and
   analysis-code hashes;
4. randomisation seed commitment and opaque arm mapping custody;
5. defect key and natural/clean gold-label commitment held outside the operator's
   writable repository;
6. power simulation and final initial N;
7. Constitution-ablation, loop, defensive, and ledger subset sizes;
8. per-call, total-call, token, wall-time, and monetary cost caps;
9. human panel membership, qualification, calibration, and conflict policy;
10. primary analysis lock template and public deviations location.

The validator must refuse dispatch while any `required_before_dispatch` value
in `config/study.yaml` or `config/models.lock.json` is null, placeholder, or
unhashed.

## 13. Stopping and interpretation

There is no efficacy or futility stopping. Operational and integrity stopping
rules are frozen in `STOPPING-RULES.md`. Reaching the cost cap, losing blinding,
model drift, excess cell-specific technical failure, or inadequate human-label
reliability stops or pauses the affected cohort; it never authorises selecting
the favourable completed cells.

All null, adverse, or incomplete results are reported. v4 can show that a
specific assignment policy improves a measured workflow under a named ruleset.
It cannot certify scientific truth, prove the provider identity behind an
unsigned API response, or eliminate shared model error.

## 14. Amendment policy

Before dispatch, corrections appear as dated amendments with rationale and
updated hashes. After the first confirmatory output exists:

- registrations, primary outcomes, matching rules, scoring, exclusions, and
  claim boundaries never change;
- necessary operational changes create a new named cohort and preserve the old
  one;
- exploratory analyses are labelled as such and cannot replace registered
  results; and
- v1–v3 files remain untouched.
