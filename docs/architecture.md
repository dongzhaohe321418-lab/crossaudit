# CrossAudit Architecture

This document is the normative description of the protocol. The READMEs summarise; where they disagree, this file wins.

## 1. Objects

| Object | Lives in | Description |
|---|---|---|
| **Experiment increment** | Science Repo | One commit (or PR) adding/altering content under `experiments/`. The unit of audit. |
| **Constitution** (`AUDIT_RULES.md`) | Audit Repo | Versioned, human-authored rulebook. Every rule: stable ID, severity, decidable acceptance criterion. |
| **Audit report** | Audit Repo, `reports/` | Structured markdown per audited increment. Must cite rule IDs and the Constitution commit hash it applied. |
| **Verdict** | Cross-repo dispatch payload + report header | `PASS` \| `BLOCKED` \| `ESCALATE`. |
| **Escalation** | Science Repo issue tracker | GitHub Issue labelled `crossaudit-escalation`, containing the report link and the round history. |
| **Config** (`crossaudit.yml`) | Science Repo | Vendors, `max_rounds`, severity policy, escalation method. |

## 2. Roles

- **Generator** — the research agent (vendor A). Produces increments; responds to audit reports (revise or dispute); never edits the Constitution or the reports.
- **Auditor** — the reviewing agent (vendor B ≠ A). Reads increments; applies the Constitution; writes reports. Has **no write access to the Science Repo** and no ability to execute the Generator's code with side effects.
- **Deterministic Check Layer (DCL)** — plain scripts (see `checks/`). Runs before the Auditor. Not a role that "decides" — a gate that *is or isn't passed*.
- **Human Principal** — authors the Constitution, receives escalations, owns final authority. Deliberately *out* of the per-increment loop.

## 3. Protocol invariants

These six invariants define CrossAudit. An implementation that breaks one is not CrossAudit.

**I1 — Heterogeneity.** The Auditor's model family/vendor differs from the Generator's. Rationale: LLM evaluators favour outputs resembling their own (self-preference bias), and same-pipeline models share failure modes; cross-vendor pairing decorrelates blind spots. It does not eliminate them — see I4 and the threat model.

**I2 — Ledger completeness.** Every protocol artifact (increment, report, verdict, dispute, escalation, Constitution change) is a commit or an issue — replayable and diffable by a third party. No supervision state lives only in platform logs or model context.

**I3 — Citation validity.** An audit report that cites no rule IDs, or cites a Constitution version other than the one at its recorded hash, is *invalid* and treated as an Auditor failure (→ escalate, not → pass).

**I4 — Determinism first.** DCL runs before any LLM audit; a DCL hard failure short-circuits to `BLOCKED` regardless of any model's opinion, and a DCL pass cannot be "un-failed" by the Auditor on the same grounds the scripts already cover. Rationale: heterogeneous LLMs still share the public literature's errors; scripted assertions are the only layer whose failure modes are fully independent of every model.

**I5 — Bounded loop.** At most `max_rounds` Generator↔Auditor exchanges per increment (default 3). Exhaustion ⇒ `ESCALATE`. This is the oscillation guard: without it, two agents can "correct" each other indefinitely, each round plausible and the pair divergent.

**I6 — Graded interruption.** Only `BLOCKER` findings gate the pipeline. `ADVISORY` findings accumulate in reports for the human to read asynchronously. Humans are interrupted only by `ESCALATE`. Compute decoupling is part of this invariant: audit outcomes gate *the next increment*, never running jobs.

## 4. Severity semantics

| Severity | Meaning | Examples | Effect |
|---|---|---|---|
| `BLOCKER` | Objective defect or hard inconsistency | DCL failure; result contradicts its own metadata; missing provenance for a reported number; unit error | Increment cannot proceed; Generator must revise or dispute |
| `ADVISORY` | Judgement-dependent concern | Basis set arguably too small; convergence threshold looser than community norm; unclear naming | Recorded; never gates |

Two levels, on purpose. Every additional level invites severity-inflation negotiations between the agents. If you find yourself wanting `MAJOR`/`MINOR`, encode the distinction in the rule's acceptance criterion instead.

## 5. Round protocol and dispute

Round *k* for increment *X*:

1. Auditor publishes report `R_k` with verdict.
2. If `BLOCKED`: Generator replies with either a **revision commit** (new increment version, loop continues at round *k+1*) or a **dispute** — a structured reply contesting specific findings *by rule ID*, with grounds.
3. A disputed finding goes back to the Auditor once. The Auditor may **withdraw** the finding (with reason, logged) or **uphold** it. An upheld, disputed `BLOCKER` at round `max_rounds` ⇒ `ESCALATE`.
4. Either agent may return `ESCALATE` at any round if it judges the matter outside its competence (the Constitution should tell it when — see rule `CA-META-003` in the template).

Disputes exist because the Auditor is fallible too: a false-positive `BLOCKER`, silently obeyed, is quality decay of a different kind. The bound (I5) keeps disputes from becoming the oscillation they are meant to prevent.

## 6. Event mechanics (reference implementation)

GitHub Actions via `repository_dispatch`:

```text
science push ──▶ [science: on-push-trigger-audit.yml]
                    └─ dispatch "crossaudit-run" {sha, changed_paths, round} ──▶ audit repo
audit repo   ──▶ [audit: run-audit.yml]
                    ├─ checkout science@sha
                    ├─ run DCL (checks/run_checks.py) → checks.json
                    ├─ run Auditor (scripts/run_llm_audit.py) → report .md
                    ├─ commit report to reports/
                    └─ dispatch "crossaudit-verdict" {verdict, report_url, round} ──▶ science repo
science repo ──▶ [science: on-audit-verdict.yml]
                    ├─ PASS → (optionally) kick Generator's next step
                    ├─ BLOCKED & round < max_rounds → notify Generator to revise/dispute
                    └─ ESCALATE or rounds exhausted → open Issue, stop this increment
```

Any CI system with cross-repo triggers can substitute; the invariants, not the YAML, are the protocol.

## 7. Threat model

| Threat | Mitigation | Residual risk |
|---|---|---|
| Self-preference / same-pipeline bias | I1 cross-vendor pairing | Shared web corpus ⇒ correlated errors persist (see next row) |
| Both vendors share a blind spot (literature itself wrong/outdated) | I4 deterministic layer for everything mechanisable | Non-mechanisable domain knowledge stays uncovered — this is the human's asynchronous reading of `ADVISORY` trails |
| **Prompt injection via experiment content** — increment text instructs the Auditor to pass it | Auditor runs with no tools and a fixed report schema; treat increment content strictly as data; DCL is immune by construction | A sufficiently capable injection could still shape the LLM report; hence injections aimed at *waiving DCL failures* are impossible, which is where hard defects land |
| Auditor failure (empty/invalid/rule-less report) | I3: invalid report ⇒ escalate, never pass | Human interruption cost |
| Oscillation (agents endlessly "correcting" each other) | I5 bounded rounds + one-shot dispute | Escalation at the bound |
| Generator gaming the rules' letter | Constitution review cadence by the human (rules are commits; drift is diffable); adversarial rule proposals welcome as PRs | Goodharting is never fully solved; decidable criteria at least make it visible |
| Secrets/credential leakage through reports | Reports render from a template with an explicit field list; CI redaction pass | Standard CI hygiene applies |

## 8. Determinism first — the longer argument {#determinism-first}

Cross-vendor pairing decorrelates *model-idiosyncratic* errors, not *corpus-inherited* ones. Claude and a GPT-family auditor were both trained on substantially the same public literature; where that literature is wrong, outdated, or systematically sloppy, both can be confidently wrong together, and the audit becomes a well-written rubber stamp. The only supervision layer with genuinely independent failure modes is one with *no learned component at all*: schema validation, dimensional analysis, conservation checks, convergence assertions, provenance completeness. This layer is narrow — it cannot judge whether a method choice is sensible — but within its scope it is incorruptible, which is exactly the property the `BLOCKER` tier needs. Hence I4: scripts before models, and no model overrides a script.

## 9. Adapting CrossAudit to another field {#adapting}

Three things change; three things don't.

**Change:** (1) the DCL check set — write assertions for whatever your field can mechanise (schema, ranges, statistical sanity, mass balance, test suites for ML claims); (2) the Constitution's domain sections — the `CA-DOM-*` rules; (3) the increment definition — what directory layout constitutes "one auditable unit".

**Keep:** the six invariants, the two-level severity, the round protocol. They are field-agnostic by construction.

A useful litmus test before adopting: *can you write ten decidable rules about your outputs?* If yes, CrossAudit will catch real defects from day one. If no — if all quality judgement in your field is irreducibly holistic — the DCL degenerates to schema checks and you are relying on I1 alone; the protocol still runs, but read §7 honestly first.
