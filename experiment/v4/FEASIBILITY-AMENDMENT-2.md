# v4 execution-feasibility cohort — Amendment 2

**Written:** 2026-09-01, after network publication and scoring of the
Amendment 1 cohort and before any call in the Amendment 2 cohort

**Applies to:** one fresh six-task feasibility cohort only

**Does not amend:** the 120-task confirmatory registration, SAP, endpoints,
task set, model configurations, claim boundary, zero-retry rule, or caps

**Claim status:** model-only, non-confirmatory engineering and measurement
feasibility; no observation is pooled across feasibility cohorts

## Why another fresh cohort is necessary

The Amendment 1 cohort is complete as an append-only record and remains the
official outcome of its freeze. It scheduled and closed 472 call records, but
only 37 provider invocations occurred. Thirty-six were valid. Invocation 37,
an OpenAI audit cell, encountered a Codex model-list refresh timeout followed
by repeated Responses WebSocket TLS-handshake EOF failures. The CLI emitted
eight top-level `error` events and one `item.completed/error` event. The frozen
event policy classified those events as a provider-event-policy violation and
correctly stopped every later dispatch. The remaining 435 scheduled cells were
retained as `safety_stop_blocked` intention-to-treat failures.

The outcome-free manifest, journal and seal were committed and network-visible
before scoring. Only then were the scientific summary and exact failure details
inspected. The published record therefore establishes that the registered
global fail-closed path worked. It does not contain enough valid cells to
estimate the seven scientific effects: no C2 artefact-auditor cell had all
three valid repeats, and the defensive-production and ledger modules received
no provider invocation.

This amendment is consequently post-outcome and cannot rescue, extend, or
reinterpret the Amendment 1 cohort. The new cohort receives a new canary,
freeze, network anchor, result directory, seal, analysis receipt and report.
Its observations are reported separately and are never pooled with either the
first aborted engineering run or Amendment 1. The purpose is to complete an
engineering-scale execution of the already frozen seven-module schedule, not
to make a confirmatory claim.

## Narrow transport-failure classification

Amendment 1 treated every Codex error-shaped event as a cohort-wide policy
violation. Amendment 2 distinguishes a content-free transport failure from an
unknown or action-bearing event. A Codex call is recorded as a non-retried,
cell-level `provider_error` and later cells may continue only when all of the
following are true:

1. every nonempty stdout line is valid JSON and every parsed entry is an
   object;
2. the exact registered three-event startup prefix is present, including the
   one byte-exact local code-mode-host-disabled notice in its fixed position;
3. every parser violation is either a top-level `error` event or an
   `item.completed/error` event;
4. after the startup prefix the event stream contains only those error shapes
   and an optional `turn.completed`; it contains no agent message, reasoning,
   command, file change, web, MCP, server-tool, or other item;
5. stderr contains the frozen Codex transport marker
   `failed to connect to websocket: IO error: tls handshake eof`.

The raw stdout envelope is discarded and retained only by SHA-256, event count
and classification evidence. Usage and cost are retained when the CLI supplied
them. The failed cell remains incorrect under intention-to-treat, and automatic
technical retries remain zero. The study never converts a failed call into a
valid observation.

Any missing startup notice, wrong position or shape, non-JSON line, unknown
event, unknown field on an otherwise allowed event, answer/reasoning content,
action item, non-zero Anthropic server-tool use, secret output, or model
identity drift keeps the Amendment 1 cohort-wide fail-closed behaviour. A
transport-looking stderr line cannot downgrade any such violation. The outer
macOS no-child-process sandbox and all disabled Codex action surfaces remain
unchanged.

## Execution and reporting controls

The direct-script sealing import is corrected so the documented `run.py` CLI
can perform the same semantic replay as package execution. This is an
execution-path repair only; it changes no task, prompt, schema, estimand,
allocation, stopping threshold or score.

The exact six tasks, two configurations, bidirectional 2×2, C0/C1/C2 and
D0/D1/D2 cells, P0/P1/P2 text and code modules, same/cross whole-loop branches,
seven ledger attacks, 42 proxy reviews, three C2 repeats, two-revision limit,
610-call ceiling, four-hour cumulative provider-invocation limit, USD 40
combined cap, USD 25 Anthropic cap, USD 40 OpenAI cap and USD 1 pre-dispatch
reserve are unchanged.

As before, operators may monitor only execution health, counts, provider
balance, cost, elapsed provider time and safety/integrity state before the
outcome-free seal is committed and network-visible. Model values, arm outcomes
and contrasts remain unread until then. The complete journal must be sealed and
pushed before scoring. All failures, nulls, adverse results and incomplete
cells are reported. No efficacy threshold is used, and the registered
120-task, human-adjudicated confirmatory study remains unrun.
