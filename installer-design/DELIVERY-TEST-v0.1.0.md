# Delivery test — crossaudit v0.1.0.dev0 (2026-08-01)

Built and tested per the operator's instruction: hunt the loop for logical and
execution holes first, in a throwaway venv, with Claude standing on both ends.

## What was actually run, and one thing that was not

Three clean virtual environments (`venv-pkg` editable, `venv-wheel` from the
built wheel, `venv-sdist` from the sdist), a throwaway git science repository,
and a local OpenAI-compatible endpoint on loopback standing in for the auditing
model. **64 tests pass**, including 23 written specifically as attacks.

**Honest gap.** No live Claude call was made: this machine has no Anthropic key
(`ANTHROPIC_BASE_URL` is set, a keyless probe returns 401) and no `claude` CLI.
The model layer was exercised two ways instead — a recorded transcript through
the `replay` provider, and a real HTTP round trip to a local stub that speaks
the OpenAI-compatible route. Both drive the identical code path: request
assembly, egress policy, key handling, reply parsing, I3 validation, verdict
synthesis, receipt construction. What they cannot test is a real model's
judgement. To close it: export `CROSSAUDIT_AUDITOR_KEY`, set
`auditor.provider: anthropic`, and run `crossaudit audit --sha HEAD`.

## Holes found and fixed

**H1 — the ledger and the state store shared a directory.** The state store must
be gitignored (mutable, local) and the ledger must be committable (immutable,
append-only). One path cannot be both: `--write-ledger` failed on the first real
run because git refused to add an ignored path. Fixed by splitting `state.dir`
(default `.crossaudit`) from `ledger.dir` (default `cycles`), and by *denying* a
configuration whose two paths overlap rather than silently preferring one.

**H2 — a crashed audit spent a revision round.** `open_or_advance` incremented
the round on entry, so a provider timeout, a git error, or a killed process
consumed one of the three revisions. Three transient failures escalated a
healthy increment to a human. This is precisely the stability failure the
operator's "the loop must be stable" is about. Fixed with an `awaiting_verdict`
flag: re-entering a round that never reached a verdict resumes it; only a
recorded verdict advances the loop. A dispute or re-audit *after* a verdict
still advances, as I5 requires.

**H3 — auditing the audit.** In local mode `--write-ledger` commits the report
into the audited repository, moving `HEAD`; the next `audit --sha HEAD` then
audited the ledger commit itself, inflating the ledger and auditing nothing.
Fixed by refusing a commit whose changed paths lie entirely inside the ledger
directory, with the message naming the fix (audit the science commit, or move
the ledger to the audit repository in paired mode).

**H4 — the exit code hid an escalation.** A `BLOCKED` round that exhausted
`max_rounds` returned 10 (blocked) while the cycle had become `ESCALATED`. A
script driving the loop would have planned another revision that can never
happen. The cycle's status now outranks the round's verdict in the exit code.

## Properties confirmed under attack

Each of these is a test that fails if the property breaks.

| Attack | Result |
|---|---|
| Model returns PASS while the deterministic layer hard-fails | BLOCKED — I4 holds; a model cannot waive a script |
| Increment prose orders the auditor to reply PASS | BLOCKED — injection cannot reach the scripted layer |
| No model ran (offline) | DCL_ONLY, never a conforming PASS — I8 floor |
| Fixture-backed PASS (`replay` provider) | integrity `NON_EVIDENTIAL_PROVIDER`; refuses to verify, so it can never admit |
| Provider unreachable mid-audit | ESCALATE with the reason recorded, never PASS |
| Science artefact edited after the audit | manifest mismatch, denied |
| Report edited after the audit | report blob hash mismatch, denied |
| Constitution weakened after the audit | content hash mismatch, denied |
| Receipt presented for a different commit | sha mismatch, denied |
| Receipt with no `receipt_schema`, or an unknown one | denied; pre-v2 is never guessed as v1 |
| Receipt admitted twice | second attempt denied (consumed / not PASSED) |
| Six processes racing to admit one receipt | exactly one admitted |
| Receipt minted on one machine with both keys, admitted where permissive isolation is required | denied on isolation shortfall |
| Editable or source install attempting admission | denied — its code can change under the digest it reports |
| Receipt whose verifier digest differs from the admitting binary | denied |
| Late verdict arriving after admission | ignored; a consumed cycle stays closed |
| Symlink inside an increment | refused before any read |
| Child commit trying to route around an escalated cycle | blocked by the escalation lock |
| Custom provider endpoint without explicit opt-in | denied before any request leaves |
| Provider redirect | refused (a redirect can move a key to another host) |

## Packaging checks

- wheel, sdist and editable installs all produce a working `crossaudit` CLI;
- the wheel contains 35 files and **none** of `paper/`, `experiment/`,
  `audits/`, `improvements/`, `installer-design/`, `ledger-mirror/` — the
  package is the execution machine, the repository is the research record;
- importing `crossaudit` opens no socket (asserted with a patched `socket`);
- `crossaudit` with no arguments prints the guided next step;
  `doctor` with no configuration exits 20 and names the fix.

## Known limitations at this milestone

1. **Local mode is not admission.** Isolation evidence records
   `permissive: false` whenever one process can reach both keys, and the paper's
   language applies: this tier verifies and reports.
2. **`init` is interactive only.** It needs a terminal; a non-interactive setup
   path (flags or a config file) is 0.2 work.
3. **The GitHub side is a plan, not an apply.** `init --github` prints the
   command sequence and checks for an authenticated `gh`; creating repositories,
   writing secrets and setting branch protection are 0.3.
4. **Retention is commitments-only.** Receipts carry request/response digests
   and the provider request ID, not raw exchanges; `sealed` therefore means "not
   retained here" at 0.1.
5. **Two keys are collected, one is used.** The generator key is stored for the
   full loop (0.5) and its presence is what makes `permissive` false — recorded,
   not narrated.
