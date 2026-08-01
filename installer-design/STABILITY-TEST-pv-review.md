# Stability test — a real project through the loop (2026-08-01)

Operator instruction: simulate a real project with Claude as both the
generating and the auditing model, run the entire flow, deliver a real PDF,
and use it to test the loop's stability. Project: a quantitative literature
review of the photovoltaic industry, built as three audited increments in a
sandbox repository (`~/crossaudit-sandbox/pv-review`).

## Setup, honestly stated

No API key exists on this machine, so "Claude on both ends" means the same
Claude instance in two roles: the generator wrote the increments; the auditor
read each committed increment fresh and produced a genuine verdict, delivered
through the `replay` provider so it traversed the identical pipeline a live
model would (prompt assembly, I3 validation, verdict synthesis, receipt).
This is the paper's v1 same-family arm, reproduced. Two consequences are
recorded rather than hidden: the auditor vendor is labelled
`anthropic-fresh-context` (vendor identity is self-declared in this protocol;
the label discloses the arm), and every PASS receipt carries
`NON_EVIDENTIAL_PROVIDER`, so nothing from this simulation can ever be
admitted as a real audit — the system itself enforces the caveat.

## What the run produced

Three increments, five audit rounds, two genuine catches:

1. **Technology increment** — the generator wrote the tandem record as 33.9%
   in prose while the data said 34.6%. The deterministic layer was clean (this
   defect is invisible to scripts); the model audit caught it, BLOCKED with
   CA-DATA-002, plus two advisories. Fix commit → PASS.
2. **Market increment** — a quantity shipped without its unit. The
   deterministic layer caught it before any model was consulted, and — with
   the auditor transcript deliberately absent — the provider failure did not
   soften the verdict: BLOCKED by I4 dominance. Fix → PASS.
3. **Paper increment** — the full LaTeX review (5 pp, 13 references); audit
   cross-checked all fifteen quantitative claims against the two audited data
   increments, PASS with one advisory worth keeping (two table values cited to
   references but not bound as quantities).

Deliverable: `pv-review.pdf`, compiled clean (0 errors, 0 overfull). Every
number in the abstract was committed and audited as data before the prose was
written.

## Six defects found in CrossAudit itself, all fixed

| # | Defect | Fix |
|---|---|---|
| S1 | **I1 never checked in offline mode**: a same-vendor pair sailed to DCL_ONLY because the heterogeneity assertion lived inside the model-call branch | `run` asserts I1 before opening a cycle whenever the model layer will run; the same-vendor config now denies up front |
| S2 | **replay provider demoted to offline**: `run` decided offline-ness by key presence, but replay needs no key | per-provider `NEEDS_KEY`; replay runs the model layer keylessly |
| S3 | **Escalation was a dead end**: DCL_ONLY → ESCALATED, and no verb existed for the human to rule on it — a keyless first-time user would jam permanently | new `crossaudit resolve <cycle> --reopen/--close --because` — I6's missing half; interactive-only, the ruling and its reason enter the ledger |
| S4 | **Re-audit vs append-only deadlock**: a human-reopened round could not write its ledger directory because round 1's already existed | attempt suffixes (`-r1.2`): the voided attempt stays beside its replacement; nothing is ever overwritten |
| S5 | **Everything was an increment**: committing a helper script forced it through the experiment format (no metadata.yml → BLOCKED noise) | `scope.dirs` in config: only commits touching the declared science directories are increments, exactly as the reference implementation's `experiments/` trigger always worked |
| S6 | *(observation, not fixed)* **Local mode dilutes round accounting**: ledger commits interleave with science commits, so a fix commit's parent is a receipt commit and opens a fresh cycle instead of advancing the blocked one. Functionally safe (every fix is audited) but I5's per-increment round budget only binds within a cycle. Vanishes in github-pair mode, where the ledger lives in the other repository; noted for 0.3 |

Also verified in passing: H2 held twice in production-like conditions (denied
runs and missing transcripts consumed no rounds); the admission gate refused
the simulation's own PASS receipts (`NON_EVIDENTIAL_PROVIDER`, exit 21); the
conversation view reconstructed the full 15-event exchange from the ledger
alone.

## Test-harness deviations, disclosed

Two actions used APIs beneath the CLI: the human escalation ruling was
recorded through `StateStore.resolve_escalation` directly because the CLI's
tty guard (correctly) refuses a scripted `resolve`, and this session has no
tty; and audit replies were recorded into the transcript directory by a
helper that mirrors `run`'s scope resolution. Neither bypassed any integrity
check; both are visible in the sandbox repository.
