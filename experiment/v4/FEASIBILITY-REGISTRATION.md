# v4 execution-feasibility cohort — prospective registration

**Registered:** 2026-09-01, before any cohort task was sent to a model
**Status:** registered engineering/measurement pilot; not confirmatory
**Relation to v4:** this cohort validates the v4 machinery and produces real,
configuration-specific pilot data. It is excluded from the 120-task
confirmatory analysis in `REGISTRATION.md`, cannot change that study's
endpoints, and cannot support a general vendor claim.

Pre-freeze model calls were limited to content-free connectivity and isolation
canaries. Earlier transient development checks were not retained and are not
treated as evidence that a control worked. After the adapters were finalised,
both configurations were rechecked with the same literal `ok=true` request.
The secret-redacted, hash-bound receipt is retained in
`feasibility/CANARY-RECEIPT.json`; it records CLI versions, exit status, schema,
usage, identity evidence and zero observed tool events. The Anthropic envelope
identifies both the requested Sonnet model and a Haiku helper; the OpenAI CLI
exposes only the requested alias, so its identity remains unverified. No canary
contained a cohort task, artefact, rulebook, audit, revision, ledger episode or
outcome, and none enters this cohort's data.

## Fixed configurations and scope

- Anthropic configuration: Claude Code CLI 2.1.252, requested model
  `claude-sonnet-4-6`, safe/restricted print mode, fresh non-persistent session,
  low effort, JSON-schema output.
- OpenAI configuration: Codex CLI 0.151.0, requested model `gpt-5.6-sol`,
  ephemeral read-only execution, ignored project/user rules, low reasoning,
  JSON-schema output.
- Both configurations receive byte-identical substantive prompts and schemas.
  Their hidden product system prompts and orchestration are not identical. The
  estimand is therefore a difference between these two configured agent
  products. It is not a pure weights effect or a vendor-population effect.
- Requested aliases and observed model-usage metadata are retained. An alias or
  hidden helper model is a limitation, not silently rewritten as a snapshot.

## Frozen pilot sample

The deterministic cohort contains the first six tasks in
`feasibility/tasks.py`, in their committed order, covering data analysis,
computational science, and scientific method. Each is sent once to both
Generators. For each vendor-authored base, the harness retains four strata:

1. the unmodified natural output;
2. an objective-field-repaired clean control that retains vendor prose;
3. a single numeric seeded defect derived from the clean control; and
4. an unusual-but-correct alternative-unit hard negative.

The model-free validator is the gold standard for this pilot only. Its task
arithmetic, accepted unit transformation, required evidence IDs, and tolerance
are frozen in `tasks.py`. No pilot finding is human-adjudicated, so finding
precision is a deterministic location-match proxy and is labelled as such.

## Seven-module execution map

1. **True bidirectional 2×2:** every Anthropic- and OpenAI-generated artefact is
   audited by both configurations. C2 core cells receive three fresh-context
   repeats.
2. **Ablation:** C0 and C1 run once on the prospectively fixed clean/seeded
   subset; C2 uses the three core repeats. D0 LLM-only, D1 deterministic-only,
   and D2 combined are reconstructed from the same replies/checks.
3. **Defensive programming/production:** both Generators receive every task in
   P0 unaware, P1 shadow-aware, and P2 hard-gate conditions in fresh sessions.
   The code-oriented subcohort uses the committed Part C fixtures or other
   committed safe fixtures. Outcomes include independent correctness plus
   words/LOC, wrappers, checks/assertions, retry/exception language,
   disclaimers, compliance-only changes, and latency. Extra content is not
   called defensive merely because it is longer.
4. **Evidence mix:** natural outputs, seeded defects, clean controls, and
   ambiguous-but-correct controls are all retained. The cohort is not a
   substitute for the registered human-gold real-task replay.
5. **Whole loop:** each seeded artefact enters both same- and cross-auditor
   branches, with at most two revision rounds by its original Generator.
   Corrections, remaining defects, new defects, unnecessary field changes,
   cost, and latency are recorded.
6. **Ledger utility proxy:** E0 final-only, E1 ordinary chronological log, and
   E2 structured hash ledger packets contain matched episode content. Each
   independently named fresh proxy-review session sees at most one surface for
   an episode; three Latin-square blocks let the same pinned model
   configuration cover all surfaces without conversational carry-over. Seeded
   stale/hash alterations are scored. These sessions are repeated calls to two
   configurations, not distinct human reviewers; this is a reconstruction
   feasibility pilot, not evidence of human usability.
7. **Reliability/statistics:** three C2 repeats are collapsed within task before
   task-clustered 2×2 contrasts. Report verdict flips, finding overlap,
   calibration, all failures under intention-to-audit, uncertainty, cost, and
   latency. With six tasks, estimates are descriptive feasibility measurements
   and no significance threshold licenses an efficacy claim.

## Caps and stopping

- maximum model calls: 600 across all modules;
- pre-dispatch combined list-price-equivalent stop: USD 40;
- pre-dispatch Anthropic list-price-equivalent stop: USD 25;
- maximum elapsed wall time: four hours per operator-started execution;
- automatic technical retries: zero. A scheduled call interrupted before its
  completion record is retained as an ITT failure on resume; malformed or
  provider-error content is likewise an outcome, not a retry;
- maximum revision rounds: two;
- no stopping for efficacy or futility;
- stop on task/arm leakage, code or prompt hash drift, model identity drift,
  wrong cell, a secret in output, or either global cap.

If a provider limit interrupts the run, every completed record remains and the
cohort is labelled incomplete. Missing cells are never filled with fabricated
values or dropped from denominators.

Before every new call, accrued observed cost plus a frozen USD 1 reserve must
fit both applicable stops. If an invoked call has unknown cost, the combined
cap is no longer verifiable and every later provider dispatch is blocked while
its scheduled cell remains an ITT failure. Claude also receives a provider-side USD 1
`--max-budget-usd` limit. Because the OpenAI CLI exposes no hard per-call
output-token or billing cap, this policy cannot guarantee that an OpenAI call
will not exceed its reserve. Any such overrun is reported and blocks all later
dispatch; the USD values are therefore scheduling stops, not promises about a
provider's ultimate invoice.

## Freeze and reporting rule

`run.py --freeze-only` must create `feasibility/FREEZE.json` from the exact
code, protocol/canary hashes, tasks, provider specifications, prompts, schemas,
CLI versions, resolved executable paths and bytes, security-route environment
hashes, sample size, repeats, and caps. The freeze is committed and pushed to a
network Git upstream before the first cohort call, and the live runner verifies
the advertised remote tip. Every provider dispatch rechecks the executable and
route binding. Every output record binds the freeze hash; resume refuses drift.

One process holds an OS-level exclusive lock on the output directory from
before manifest/journal access through scoring. A concurrent process exits
before dispatch, rather than racing call, cost, or safety state.

Raw envelopes are append-only and every journal event hashes its predecessor;
loading refuses a broken chain. The scored report must state all denominators,
failed calls, task-clustered intervals, exact configurations, list-price-
equivalent cost where available, and the difference between deterministic gold,
model-reviewer proxy evidence, and the still-unrun human confirmatory study.
