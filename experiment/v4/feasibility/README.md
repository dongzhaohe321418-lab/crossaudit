# v4 execution-feasibility cohort

This directory contains a runnable, deliberately small pilot of the v4 causal
design. It exercises the complete harness and produces real model observations,
but it is **not** the registered confirmatory cohort. Its six deterministic
convenience tasks, two pinned CLI/model configurations and model-proxy ledger
reviewers cannot support a general vendor or product claim. The registered
120-task, human-adjudicated study has not been run; this replacement six-task,
model-only cohort is non-confirmatory feasibility evidence.

The replacement cohort is governed by
[`FEASIBILITY-REGISTRATION.md`](../FEASIBILITY-REGISTRATION.md) and
[`FEASIBILITY-AMENDMENT-1.md`](../FEASIBILITY-AMENDMENT-1.md).

The pilot covers all seven v4 design questions at feasibility scale:

1. a complete, bidirectional generator × auditor 2×2;
2. C2 in three fresh repeats, with prospective C0/C1 clean-and-seeded subsets
   limited to one data-analysis and one computational-science task;
3. offline reconstruction of D0 model-only, D1 deterministic-only and D2
   combined-blind decisions from the same calls;
4. natural outputs, deterministic clean controls, single seeded errors and
   unusual-but-correct alternate-unit controls;
5. P0 unaware, P1 shadow-aware and P2 hard-gate production, with at most two
   immutable revision rounds;
6. E0 final-only, E1 transcript and E2 hash-bound ledger surfaces with seeded
   tamper challenges and Latin-square proxy-review allocation; and
7. append-only execution records, intention-to-treat failures, frozen prices,
   latency and cost, and task-clustered descriptive scoring.

The defensive-production module includes both compact research JSON and a
scientific-Python sub-cohort. The latter reports LOC, extra wrappers,
assertions, exception/retry constructs, disclaimers, visible correctness and
held-out correctness. Model code is statically restricted and then evaluated
only in an isolated `python -I -S` child with a timeout and resource limits; it
is never executed in the experiment runner.

## Freeze before any call

After the runner, adapters, validator and protocol text are final, run the
content-free isolation canary. This makes exactly one `ok=true` call to each
pinned provider and replaces the receipt only if both calls and local
self-validation pass. Any later change to a canary dependency invalidates the
receipt and requires a new canary.

Codex CLI 0.151.0 labels its deterministic “code-mode host disabled; fail
closed” startup notice as an error item. The parser admits exactly one instance
of that byte-exact message and three-field item shape with `id=item_0` only as
the second nonempty event after
`thread.started` and before `turn.started`, records its named notice ID, and
rejects every other error or action event. A frozen config override suppresses
the unrelated unstable-feature warning; the outer sandbox still denies all
child execution.

```bash
python experiment/v4/feasibility/canary.py --execute --timeout 300
```

Create a price file without credentials. Prices are USD per million tokens.
Use the pinned public/list-equivalent rates selected by the study lead. Explicit
zero prices are accepted only when zero marginal charge is the frozen costing
assumption; Claude's own `total_cost_usd` envelope takes precedence when
available.

```json
{
  "currency": "USD",
  "prices": {
    "anthropic/claude-sonnet-4-6": {
      "input_per_million": 3.0,
      "cached_input_per_million": 0.3,
      "output_per_million": 15.0
    },
    "openai/gpt-5.6-sol": {
      "input_per_million": 4.0,
      "cached_input_per_million": 0.4,
      "output_per_million": 20.0
    }
  }
}
```

Generate the freeze. This command only reads CLI versions and local files; it
makes no model call.

```bash
python experiment/v4/feasibility/run.py \
  --freeze-only \
  --prices-json experiment/v4/feasibility/prices-2026-09-01.json \
  --n-tasks 6 \
  --constitution-subset 2 \
  --cost-cap-usd 40 \
  --anthropic-cap-usd 25 \
  --openai-cap-usd 40
```

`FREEZE.json` binds the selected tasks, providers/models, CLI versions, resolved
CLI/native executable paths and hashes, security-route environment hashes,
protocol/canary documents, rendered prompt and Constitution hashes, schemas,
code hashes, three-repeat policy, zero-retry policy, revision limit,
randomisation seed, prices, total USD 40 cap and provider caps.
It labels the cohort non-confirmatory. Inspect it, then commit and push it:

```bash
git add experiment/v4/feasibility/FREEZE.json
git commit -m "Register v4 feasibility execution freeze"
git push
```

Live execution fails closed unless the exact freeze is tracked, clean and the
commit containing it is present at the network-advertised tip of the registered
`github.com` upstream over HTTPS or SSH. Plaintext `git://`, numeric/IP aliases
and other hosts are rejected. Code,
prompts, protocol evidence, executable bytes, route settings,
CLI versions, prices or arguments that differ from the freeze also stop
execution before a model call. Executable/route bindings are rechecked before
every actual provider dispatch. Pre-dispatch verification compares the current
`FREEZE.json` bytes with `git show` from its containing commit, rechecks those
bytes before returning, disables Git replace objects, and rejects replacement
refs or legacy graft files; a clean-looking index flag cannot substitute a
different local freeze or ancestry graph.

## Execute and resume

Pass exactly the same frozen options plus `--execute` and a result directory:

```bash
python experiment/v4/feasibility/run.py \
  --execute \
  --prices-json experiment/v4/feasibility/prices-2026-09-01.json \
  --n-tasks 6 \
  --constitution-subset 2 \
  --cost-cap-usd 40 \
  --anthropic-cap-usd 25 \
  --openai-cap-usd 40 \
  --output experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1
```

The complete six-task schedule permits at most 610 provider calls; successful
P2 outputs use fewer because revision stops after a passing gate. Use
`--n-tasks 1` only for a separately frozen end-to-end smoke cohort. Do not
reduce unfavourable directions or repeats after looking at output.

The live feasibility harness is currently macOS-local: the OpenAI adapter uses
the native binary inside a `sandbox-exec` profile that forbids child processes,
and the Anthropic adapter supplies an empty tool set plus restricted/strict MCP
settings. Before the replacement freeze, `CANARY-RECEIPT.json` must contain the
post-hardening, content-free canary receipt required by Amendment 1. The prior
pre-hardening receipt and earlier transient checks are historical connectivity
evidence only and do not satisfy this prerequisite. These controls do not
constitute a portable production sandbox. The two CLIs must already be
authenticated through their normal local login.
The runner stores no API key. Each call uses an ephemeral fresh context and no
tools. `events.jsonl` is append-only and every event hashes its predecessor: a
schedule event is flushed before dispatch, followed by one completion event.
Loading refuses a modified, removed, inserted, or reordered prior event. On
resume, a scheduled call lacking
a completion is recorded as `interrupted` and scored incorrect; it is not
silently retried. Provider, parse, timeout, upstream, unknown-cost and budget
failures likewise remain explicit intention-to-treat rows. Because the USD 40
limit applies to the combined cohort, one invoked call with unknown cost makes
that limit unverifiable and blocks every later provider dispatch. The remaining
scheduled cells are still written as `budget_unverifiable` ITT outcomes.

One process holds a non-blocking OS lock on the result directory from before
manifest/journal access through terminal structural/semantic validation and
creation of the outcome-free cohort seal. Standalone sealing and scoring each
reacquire the same retained lock file. A concurrent process therefore exits
before it can race journal, seal, cost, or safety state; the lock is released
between the run/seal stage and the later score stage while the Git anchor is
created.

The four-hour execution stop is not operator wall-clock time. It is the frozen
cap on the sum of `elapsed_seconds` for calls for which provider invocation
actually occurred, reconstructed from the journal on resume. Time spent between
commands, committing/pushing the seal, or in deterministic scoring does not
consume that cap. Once the cumulative provider-invocation elapsed time reaches
the cap, later scheduled calls are retained as `elapsed_cap_blocked` ITT rows.

The USD 40/25 values are fail-closed **pre-dispatch stops**: before a call, the
runner requires accrued observed cost plus the frozen USD 1 single-call reserve
to fit both limits. Claude additionally receives its USD 1 provider-side
`--max-budget-usd` cap. The OpenAI CLI does not expose a hard output-token/budget
flag, so these values are not an absolute billing guarantee; a call could
exceed its reserve. Any overrun is reported. A combined-cap overrun stops every
later dispatch; an overrun of only one provider's cap stops later calls to that
provider while the other may continue within the combined cap. The freeze
records this limitation explicitly.

Before persistence, provider envelopes are scanned for common API-key, GitHub,
AWS and private-key patterns. A match is discarded (only its hash and pattern
label remain), marks the call invalid and stops later dispatch. When model
identity metadata is available it must include the requested alias; drift also
stops dispatch. OpenAI's current CLI does not report an authoritative resolved
model ID, so that identity remains unverified rather than being filled with the
requested alias.

The result directory's `run_manifest.json` is permanently bound to the freeze
hash. Re-running the same command and output directory is idempotent and resumes
missing deterministic work without overwriting prior events.

## Seal, anchor, then score

Execution ends by structurally and semantically validating the terminal journal
and writing `COHORT-SEAL.json`. That outcome-free seal binds the exact manifest
and journal bytes, final event, event/call counts and non-confirmatory claim
boundary; it deliberately contains no endpoint summary. If a terminal journal
needs to be sealed separately, use:

```bash
python experiment/v4/feasibility/score.py \
  --seal-only experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1
```

Before scoring, commit and push exactly the raw run and seal in a commit that is
distinct from the pre-dispatch freeze commit. Do not include `summary.json` or
`ANALYSIS-RECEIPT.json` in this pre-analysis commit:

```bash
git add \
  experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1/run_manifest.json \
  experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1/events.jsonl \
  experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1/COHORT-SEAL.json
git commit -m "Seal v4 feasibility cohort before analysis"
git push
```

Only after that push may the endpoint scorer run:

```bash
python experiment/v4/feasibility/score.py \
  experiment/v4/feasibility/results/2026-09-01-six-task-amendment-1
```

Before calculating endpoints, the scorer reacquires the result lock and verifies
that the freeze, manifest, journal and add-once seal are tracked and clean; the
seal commit contains no scientific output; the recorded pre-dispatch network tip
contains the distinct freeze commit and precedes the seal commit; and the
network-advertised upstream contains the seal commit with the exact snapshotted
bytes. It rejects shallow repositories and checks the seal path from the
network-advertised tip, requiring exactly one path-changing commit and one
addition, both equal to the seal commit. It then writes `summary.json` and
`ANALYSIS-RECEIPT.json`. The latter binds
the summary and cohort-seal hashes, freeze and seal commits, pre-dispatch and
first-analysis network tips, completion/withholding status and claim boundary.
It writes the receipt before the deterministic summary so a crash can resume
from a receipt-only state; a pre-existing summary without its matching receipt
is rejected as an untrusted orphan.
Commit and push those two analysis artefacts after review; they never belong in
the pre-analysis seal commit.

This mechanism controls the official runner/scorer path, not a hostile operator
with repository read access. Before the seal commit is present on the network
upstream, operators and agents must not read provider `value` fields, arm
outcomes or contrasts and must not import or call `build_summary`. Only the
prospectively listed execution-health checks—event/call counts, provider
balance, accrued cost, elapsed time, stop state and safety/integrity errors—may
be inspected. Git history is evidence of the official artefact sequence, not a
proof that no privileged process ever read raw bytes.

The summary reports raw cell counts and failures, a fixed-weight
clean/seeded/ambiguous-correct controlled-accuracy 2×2 (and equal-weight
clean/ambiguous false-block 2×2) after repeat-within-task collapse, generator
and auditor main effects in both directions, their interaction, natural-output
available-case performance, separate Constitution×DCL contrasts, P0/P1/P2
initial and delivered-final overhead/correctness, bounded-loop
repair/regression, interface- and attack-specific ledger accuracy/Brier/raw and
capped decision latency, tokens and cost. With at most six tasks, every
interval is labelled descriptive feasibility output.

For the controlled core, a task contributes only when all four frozen
Generator×Auditor directions and every prospectively weighted stratum are
present after repeat collapse; missing directions/strata are listed as an
incomplete task, never replaced by a realised-row average. Natural output uses
the same complete-four-cell rule but remains an available-gold descriptive
stratum.

Whole-loop comparisons use strict complete-branch weighting: each task must
contain every frozen Generator branch in both same- and cross-auditor levels.
Incomplete clusters are listed and do not receive an opportunistic partial-cell
weight. If a seeded or final artefact is unavailable, repair and final
acceptability are zero under ITT, while new-defect and unnecessary-change harms
are unknown rather than imputed as safe. Ledger output includes E2−E0,
E2−E1 and E1−E0 episode-clustered contrasts, resource totals for every
interface/attack cell, raw ITT latency (including deterministic zeroes for
non-invoked blocked calls), and separate provider-invoked latency. Ledger
contrasts likewise require the two frozen configuration rows per interface and
explicitly list incomplete episodes.

## Interpretation boundaries

- `clean` and `ambiguous` are deterministic negative controls derived from a
  vendor-authored base; `seeded` contains one deterministic numeric mutation;
  `natural` is unmodified generator output. They are not pooled without labels.
- The same frozen checker supplies micro-task ground truth and D1. D1 accuracy
  is therefore a harness ceiling check, not an unbiased estimate of DCL value.
- C0/C1 are instantiated only on `F-DATA-01` and `F-SCI-01`. There is no
  C0/C1 estimate for the scientific-method domain in this cohort; C2 coverage
  elsewhere cannot be used to infer that missing ablation.
- Defensive `functional_improvement`, `harmful`, `quality_changed`,
  `necessary_evidence`, `compliance_only`, `defensive_disclaimer` and `neutral`
  labels are deterministic
  P0-relative proxies. They use the frozen objective/fixture checks and observable
  counts of checks, limitations, wrappers, assertions, exception/retry constructs
  and disclaimers. They are not semantic or human change adjudication, and length
  alone is not classified as defensive programming.
- Ledger calls use fresh model sessions as reviewer proxies. The Latin square
  assigns each independently named proxy block only one surface per episode.
  The same pinned provider/model configuration is replicated across three such
  fresh blocks and is not a persistent human-style reviewer identity. Provider
  latency is a feasibility proxy, not human reconstruction time.
- Each of the seven attacks has only one episode and is therefore confounded
  with that episode/task. Attack-specific tables are descriptive integrity
  diagnostics, not estimates of an attack-class effect. Allocation IDs remain
  journal metadata and are not exposed to one interface as a treatment cue.
- The confirmatory claims still require the registered task scale, independent
  Gold and Matching Panels, external escrow, blinded analysis and the full SAP;
  none of those 120-task human-study requirements is satisfied by this cohort.
- The network Git check is an external ancestry witness at verification time,
  not a cryptographic transparency log or an immutable timestamp. A mutable
  branch can later be force-pushed, and a compromised host or remote administrator
  can rewrite history. The recorded commit/tip hashes make such divergence
  detectable only while an independent copy or later descendant remains
  available; durable claims require an append-only archive or independent
  timestamp in addition to this feasibility control.
