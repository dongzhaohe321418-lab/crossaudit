# v4 execution-feasibility cohort

This directory contains a runnable, deliberately small pilot of the v4 causal
design. It exercises the complete harness and produces real model observations,
but it is **not** the registered confirmatory cohort. Its six deterministic
convenience tasks, two pinned CLI/model configurations and model-proxy ledger
reviewers cannot support a general vendor or product claim.

The pilot covers all seven v4 design questions at feasibility scale:

1. a complete, bidirectional generator × auditor 2×2;
2. C2 in three fresh repeats, with prospective C0/C1 clean-and-seeded subsets;
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
      "input_per_million": 0,
      "cached_input_per_million": 0,
      "output_per_million": 0
    },
    "openai/gpt-5.6-sol": {
      "input_per_million": 0,
      "cached_input_per_million": 0,
      "output_per_million": 0
    }
  }
}
```

Generate the freeze. This command only reads CLI versions and local files; it
makes no model call.

```bash
python experiment/v4/feasibility/run.py \
  --freeze-only \
  --prices-json experiment/v4/feasibility/prices.local.json \
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
commit containing it is present at the network-advertised tip of a non-file
upstream. Code, prompts, protocol evidence, executable bytes, route settings,
CLI versions, prices or arguments that differ from the freeze also stop
execution before a model call. Executable/route bindings are rechecked before
every actual provider dispatch.

## Execute and resume

Pass exactly the same frozen options plus `--execute` and a result directory:

```bash
python experiment/v4/feasibility/run.py \
  --execute \
  --prices-json experiment/v4/feasibility/prices.local.json \
  --n-tasks 6 \
  --constitution-subset 2 \
  --cost-cap-usd 40 \
  --anthropic-cap-usd 25 \
  --openai-cap-usd 40 \
  --output work/v4-feasibility-live
```

The complete six-task schedule permits at most 598 provider calls; successful
P2 outputs use fewer because revision stops after a passing gate. Use
`--n-tasks 1` only for a separately frozen end-to-end smoke cohort. Do not
reduce unfavourable directions or repeats after looking at output.

The live feasibility harness is currently macOS-local: the OpenAI adapter uses
the native binary inside a `sandbox-exec` profile that forbids child processes,
and the Anthropic adapter supplies an empty tool set plus restricted/strict MCP
settings. A final content-free recheck and its secret-redacted evidence are in
`CANARY-RECEIPT.json`; earlier transient development checks were not retained
and are not treated as evidence. These controls do not constitute a portable
production sandbox. The two CLIs must already be authenticated through their
normal local login.
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
manifest/journal access through final scoring. A concurrent second runner exits
before any model dispatch, so it cannot duplicate a call or race the cost and
safety stops.

The USD 40/25 values are fail-closed **pre-dispatch stops**: before a call, the
runner requires accrued observed cost plus the frozen USD 1 single-call reserve
to fit both limits. Claude additionally receives its USD 1 provider-side
`--max-budget-usd` cap. The OpenAI CLI does not expose a hard output-token/budget
flag, so these values are not an absolute billing guarantee; a call could
exceed its reserve. Any overrun stops later dispatch and is reported. The
freeze records this limitation explicitly.

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

## Score

Execution writes `summary.json` automatically. It can be regenerated from the
immutable journal:

```bash
python experiment/v4/feasibility/score.py work/v4-feasibility-live
```

The summary reports raw cell counts and failures, C2 cross-minus-same gate
accuracy and clean false blocks, Constitution and DCL contrasts, repeat flips,
P0/P1/P2 overhead and held-out correctness, bounded-loop repair/regression,
ledger reconstruction/tamper proxies, tokens, list/frozen-price cost and
latency. Repeats and artefact variants are averaged inside task before an
interval is computed. With at most six tasks, every interval is labelled
descriptive feasibility output.

## Interpretation boundaries

- `clean` and `ambiguous` are deterministic negative controls derived from a
  vendor-authored base; `seeded` contains one deterministic numeric mutation;
  `natural` is unmodified generator output. They are not pooled without labels.
- The same frozen checker supplies micro-task ground truth and D1. D1 accuracy
  is therefore a harness ceiling check, not an unbiased estimate of DCL value.
- Ledger calls use fresh model sessions as reviewer proxies. The Latin square
  assigns each independently named proxy block only one surface per episode.
  The same pinned provider/model configuration is replicated across three such
  fresh blocks and is not a persistent human-style reviewer identity. Provider
  latency is a feasibility proxy, not human reconstruction time.
- The confirmatory claims still require the registered task scale, independent
  Gold and Matching Panels, external escrow, blinded analysis and the full SAP.
