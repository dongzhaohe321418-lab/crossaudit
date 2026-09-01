# v4 execution-feasibility cohort — prospective registration

**Registered:** 2026-09-01, before any cohort task was sent to a model
**Status:** registered engineering/measurement pilot; not confirmatory
**Relation to v4:** this cohort validates the v4 machinery and produces real,
configuration-specific pilot data. It is excluded from the 120-task
confirmatory analysis in `REGISTRATION.md`, cannot change that study's
endpoints, and cannot support a general vendor claim. The 120-task,
human-adjudicated study remains unrun; the replacement six-task cohort described
here is model-only, non-confirmatory feasibility work.

The replacement cohort is additionally governed by
[`FEASIBILITY-AMENDMENT-1.md`](FEASIBILITY-AMENDMENT-1.md); where it changes
this document, the amendment controls.

Before the original, subsequently aborted freeze, model calls were limited to
content-free connectivity and isolation canaries. Earlier transient development
checks were not retained and are not treated as evidence that a control worked.
The aborted cohort's 33 completed calls and one interrupted schedule are
documented and excluded by Amendment 1; no cohort-content call is used to tune
the replacement protocol. With the then-current adapters,
both configurations were rechecked with the same literal `ok=true` request.
The then-retained secret-redacted, hash-bound receipt recorded CLI versions,
exit status, schema, usage, identity evidence and zero observed tool events.
The Anthropic envelope identified both the requested Sonnet model and a Haiku
helper; the OpenAI CLI exposed only the requested alias, so its identity
remained unverified. That pre-hardening receipt predates the later local Codex
feature allowlist and fail-closed event parser and is historical connectivity
evidence only. Amendment 1 requires `feasibility/CANARY-RECEIPT.json` to be
replaced by a content-free post-hardening receipt before the replacement freeze.
No qualifying canary contains a cohort task, artefact, rulebook, audit, revision,
ledger episode or outcome, and none contributes an observation.

## Fixed configurations and scope

- Anthropic configuration: Claude Code CLI 2.1.252, requested model
  `claude-sonnet-4-6`, safe/restricted print mode, fresh non-persistent session,
  low effort, JSON-schema output.
- OpenAI configuration: Codex CLI 0.151.0, requested model `gpt-5.6-sol`,
  ephemeral read-only execution, ignored user configuration and project rules,
  strict configuration parsing, skipped host-skill discovery, low reasoning,
  JSON-schema output, and explicit feature overrides disabling plugins, apps,
  shell, browser, computer-use, MCP-app, hook, image, multi-agent, and skill
  surfaces where this CLI permits it. `unified_exec` remains effectively true
  in this pinned CLI despite a disable override; an outer `sandbox-exec` profile
  denies every child process and any command/file/web/MCP event is nevertheless
  a cohort-stopping policy violation. Codex 0.151.0 emits one deterministic
  `item.completed/error` startup notice because its code-mode host is disabled;
  the adapter accepts only that exact fail-closed message, three-field item
  shape with `id=item_0`, and
  count in the fixed second-nonempty-event position immediately after
  `thread.started` and before `turn.started`, records its named notice ID, and rejects
  every other error event. The
  separate unstable-feature warning is suppressed by a frozen CLI override.
- Both adapters use the exact neutral system instruction `Follow the user task.
  Do not use tools. Return only the object required by the supplied output
  schema.` Role and arm labels remain journal metadata and are not inserted in
  either provider's instruction prefix.
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
The constitution ablation subset is fixed to `F-DATA-01` and `F-SCI-01`, one
data-analysis and one computational-science task. C0/C1 are not instantiated in
the scientific-method domain, so this cohort has no method-domain C0/C1
estimand. Method-domain C2 observations do not fill that missing ablation.

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
   called defensive merely because it is longer. P0-relative change labels are
   deterministic code/artefact proxies based on frozen correctness checks and
   observable structures; they are not blinded semantic change adjudication.
4. **Evidence mix:** natural outputs, seeded defects, clean controls, and
   ambiguous-but-correct controls are all retained. The cohort is not a
   substitute for the registered human-gold real-task replay.
5. **Whole loop:** each seeded artefact enters both same- and cross-auditor
   branches, with at most two revision rounds by its original Generator.
   Corrections, remaining defects, new defects, unnecessary field changes,
   cost, and latency are recorded. An unavailable seeded or final artefact is
   zero repair and zero final acceptability under ITT; whether it introduced a
   new defect or an unnecessary change is unknown, not imputed as no harm.
   Same−cross contrasts require all frozen Generator branches in both levels
   for a task and expose rather than partially reweight incomplete clusters.
6. **Ledger utility proxy:** E0 final-only, E1 ordinary chronological log, and
   E2 structured hash ledger packets contain matched episode content. Each
   independently named fresh proxy-review session sees at most one surface for
   an episode; three Latin-square blocks let the same pinned model
   configuration cover all surfaces without conversational carry-over. Seeded
   stale/hash alterations are scored. These sessions are repeated calls to two
   configurations, not distinct human reviewers; this is a reconstruction
   feasibility pilot, not evidence of human usability. Reports include E2−E0,
   E2−E1 and E1−E0 episode-clustered contrasts, resource totals by
   interface and attack, raw ITT latency and separate provider-invoked latency.
   Each contrast requires both frozen configuration rows per interface for the
   episode and exposes incomplete episodes rather than silently reweighting them.
7. **Reliability/statistics:** three C2 repeats are collapsed within task before
   task-clustered 2×2 contrasts. Report verdict flips, finding overlap,
   calibration, all failures under intention-to-audit, uncertainty, cost, and
   latency. A task enters a controlled 2×2 contrast only with all four frozen
   Generator×Auditor directions and all prospectively weighted strata; missing
   cells are exposed, not reweighted by their realised availability. With six
   tasks, estimates are descriptive feasibility measurements and no significance
   threshold licenses an efficacy claim.

## Caps and stopping

- maximum model calls: 610 across all modules;
- pre-dispatch combined list-price-equivalent stop: USD 40;
- pre-dispatch Anthropic list-price-equivalent stop: USD 25;
- maximum cumulative provider-invocation elapsed time: four hours, defined as
  the sum of journaled `elapsed_seconds` only for calls with
  `provider_invoked=true`; it is reconstructed on resume and is not an operator
  wall-clock deadline;
- automatic technical retries: zero. A scheduled call interrupted before its
  completion record is retained as an ITT failure on resume; malformed or
  provider-error content is likewise an outcome, not a retry;
- maximum revision rounds: two;
- no stopping for efficacy or futility;
- stop on task/arm leakage, code or prompt hash drift, model identity drift,
  wrong cell, a secret in output, a provider event outside the no-action
  allowlist, or either global cap. Non-zero Anthropic server-tool use and Codex
  command execution, file change, web search, MCP, error, malformed, or unknown
  events all use the same `provider_event_policy_violation` stop.

If a provider limit interrupts the run, every completed record remains and the
cohort is labelled incomplete. Missing cells are never filled with fabricated
values or dropped from denominators.

Before every new call, accrued observed cost plus a frozen USD 1 reserve must
fit both applicable stops. If an invoked call has unknown cost, the combined
cap is no longer verifiable and every later provider dispatch is blocked while
its scheduled cell remains an ITT failure. Claude also receives a provider-side USD 1
`--max-budget-usd` limit. Because the OpenAI CLI exposes no hard per-call
output-token or billing cap, this policy cannot guarantee that a call will not
exceed its reserve. Any overrun is reported. Exceeding the combined USD 40 cap
blocks every later dispatch; exceeding only a provider-specific cap blocks
later calls to that provider while the other provider may continue within the
combined cap. The USD values are therefore scheduling stops, not promises
about a provider's ultimate invoice.

## Freeze and reporting rule

`run.py --freeze-only` must create `feasibility/FREEZE.json` from the exact
code, protocol/canary hashes, tasks, provider specifications, prompts, schemas,
neutral system instruction, CLI versions, resolved executable paths and bytes,
the exact Codex command template, requested and locally observed feature state,
event allowlist including the exact local fail-closed notice hash/count, outer
sandbox profile, security-route environment hashes,
sample size, repeats, and caps. The freeze is committed and pushed to a
registered `github.com` Git upstream over HTTPS or SSH before the first cohort
call (plaintext `git://`, numeric/IP aliases and other hosts are rejected), and
the live runner verifies
the advertised remote tip. It exact-compares the live freeze bytes with the
containing commit, disables replace objects, and rejects replacement refs and
legacy grafts before accepting any ancestry proof. Every provider dispatch
rechecks the executable and route binding. Every output record binds the freeze
hash; resume refuses drift.

One process holds an OS-level exclusive lock on the output directory from
before manifest/journal access through terminal validation and outcome-free
sealing. Standalone sealing and scoring reacquire the same retained lock file;
the lock is released while the operator creates the required Git anchor between
those stages. A concurrent process exits before racing journal, seal, call, cost,
or safety state.

Raw envelopes are append-only and every journal event hashes its predecessor;
loading refuses a broken chain. Reporting follows a mandatory two-stage reveal:

1. after the terminal event, the runner validates the complete structure and
   semantics and creates `COHORT-SEAL.json` without calculating or storing a
   scientific summary. The seal binds the exact manifest/journal bytes, final
   event and counts. The operator commits and pushes the manifest, journal and
   seal, without `summary.json` or `ANALYSIS-RECEIPT.json`, in a commit distinct
   from the pre-dispatch freeze commit;
2. only after the network-advertised upstream contains that add-once seal commit
   may `score.py` calculate endpoints. It verifies the exact snapshotted bytes,
   the freeze/start/seal ancestry, a complete non-shallow history in which the
   advertised remote tip shows exactly one seal-path commit and one addition,
   and absence of scientific outputs in the seal commit, then creates
   `summary.json` and `ANALYSIS-RECEIPT.json`. The analysis
   receipt binds the summary/seal bytes and the pre-dispatch, seal and
   first-analysis Git anchors. The scorer writes the receipt before the
   deterministic summary so a crash leaves a resumable receipt-only state;
   an existing summary without a receipt is rejected as an untrusted orphan.

The seal constrains the official CLI path but cannot prevent a privileged local
operator from opening the journal or importing the public scoring function.
Until the seal commit is network-visible, operators and agents must not inspect
provider `value` fields, arm outcomes or contrasts and must not directly invoke
`build_summary`. Permitted monitoring is limited to event/call counts, provider
balance, accrued cost, cumulative provider elapsed time, stop state, and
safety/integrity errors. The Git/receipt chain records the official sequence; it
does not prove the absence of every out-of-band read on a compromised host.

The scored report must state all denominators, failed calls, incomplete
clusters, task-clustered intervals, exact configurations, list-price-equivalent
cost where available, and the difference between deterministic gold,
model-reviewer proxy evidence, and the still-unrun human confirmatory study.

This network check witnesses branch ancestry at the moments of dispatch and
analysis; it is not an immutable timestamp or transparency log. A force-push,
remote administrator or compromised host can later rewrite a mutable branch.
The recorded hashes support detection only while an independent copy or
descendant survives. Any durable evidentiary claim therefore needs an
append-only archive or independent timestamp beyond this feasibility control.
