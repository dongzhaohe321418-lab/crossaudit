# Revision 2 roadmap — the distance between specification and enforcement

Source: the two cross-vendor audits committed under `audits/`. Revision 1 closed the
validator, scoping, payload-injection, and offline-PASS holes; this file enumerates,
without euphemism, what must exist before the reference implementation may claim to
*enforce* I7/I8 rather than target them.

1. **Protected controller state.** A state machine per logical increment: `cycle_id`,
   `root_sha`, `active_sha`, `parent_receipt`, status, retry nonce, and a
   consumed-receipts set — held where neither agent can write (protected branch or
   external store). Rounds are controller-managed per cycle, not derived from
   changed-path sets (which reset on a nonce file and collide across unrelated commits).
2. **Receipt verification, fully bound.** The callback carries only a receipt
   reference. The controller fetches the receipt from the *configured* audit repo at a
   full-SHA commit (done in R1) and additionally verifies: science repo identity,
   resolved commit and tree, manifest against the fetched tree, Constitution/DCL/prompt
   /policy hashes, report blob hash, parent state, and freshness against `active_sha`
   (a stale PASS for S0 must not admit S1). Report URLs must be immutable permalinks.
3. **A real admission gate.** Wire the controller verdict into a required status check
   / merge queue / deployment gate so a protected action can actually be refused.
   Post-push summaries are notifications; they must never be described as admission.
4. **Immutable cycle artifacts.** Full-SHA, non-overwritable cycle directories (R1 uses
   full-SHA names; overwrite protection and branch protection remain); receipts extended
   with report blob hash and ledger commit via a two-phase commit.
5. **Scope = push range + dependency closure.** Audit `before..after` of the push (not
   `HEAD^..HEAD`, which under-covers multi-commit pushes); include declared dependencies
   in the manifest; escalate on truncation/missing/symlink (R1 escalates; containment
   checks on paths remain).
6. **Raw exchange capture.** Store or verifiably commit to full model requests/responses,
   parameters, provider identity and request IDs, timestamps, and failure traces (the
   experiment runner records digests since R1; the audit runner must too).
7. **Dispute/re-audit machinery.** Explicit dispute handler, re-audit trigger, timeout
   and dead-letter escalation; router-side escalation on `audit_integrity !=
   OK`.
8. **Separated credentials.** Distinct minimal-scope tokens per direction; no shared
   dispatch secret across both workflows.
9. **Experiment v2** per `experiment/v2-REGISTRATION.md`: matched frozen arms, per-defect
   single-finding binding, blinded independent adjudication, L3-only and out-of-scope
   controls, CIs and full alarm-burden reporting, corpora authored by each vendor's
   generator so same-source effects are actually testable.

Until these land, the honest description of the public implementation is: **targets
I1–I8; implements deterministic checks, reply validation, receipts, and anchored
callbacks; does not yet enforce receipt-verified fail-closed admission.**


## Status after commit 96c012b

✅ done: 1, 2, 4, 8 · ◐ partial: 3 (status posted; protection is a deployer toggle),
5 (range done; dep-closure/containment open), 6 (digests+parsed; raw bodies open),
7 (dispute+deadletter; integrity-escalation open), 9 (scorer done; execution blocked
on operator keys/escrow) · Locally tested: DCL_ONLY→deny, PASS→admit+consume,
replay→deny, tamper→deny, controller round derivation.

## R3 candidate: telemetry-driven standards ratchet

Shadow-mode rule promotion (ADVISORY rehearses enforcement; ledger evidence — hit rate,
dispute rate, would-be blocking cost — justifies promotion to BLOCKER); stepwise threshold
tightening as generator competence grows; agent-drafted amendment PRs from ledger telemetry
(auto-draft promotion after N undisputed hits; auto-draft clarification after M
disputed-and-withdrawn), with enactment reserved to the human principal. Invariant: standards
freeze within a cycle (I7 pins the version) and move only between cycles, preserving I5
termination.

## R4 candidate: distribution and interface

**Packaging.** `pip install crossaudit`: controller, receipt verifier, DCL runner and
scaffolding (`crossaudit init` / `audit` / `verify --admit`) as a release-versioned CLI.
Receipts extended to record the verifier's package version and distribution hash — vendored
copies drift, and a receipt that does not pin the machinery that admitted on its basis is
bound one layer short of I7's intent. Field check packs as extras (`crossaudit[compchem]`).
New trust surface: package supply chain (signed releases, hash-pinned installs).

**Supervision console.** A UI over the ledger: per-increment cycle timelines, advisory
backlog by rule and hit rate, escalation inbox (round history, diffs, dispute grounds),
ratchet telemetry. Hard rule: the console writes nothing of its own — every action
materialises as a commit or issue through the agents' own authenticated paths (I2);
a private store would be a second, unauditable ledger.

## Post-detread status (third audit, wiring fixes)
Fixed: --admit live in router (state machine on execution path); verifier report path
follows the receipt's own cycle dir (dispute rounds verify); anchor checkout births HEAD +
"unversioned" constitution now DENIES; MAX_ROUNDS read from crossaudit.yml; same-sha
re-dispatch advances rounds (no cycle reset), ESCALATED unbypassable by child commits;
deadletter dedup via state writeback; run-audit concurrency group; example README ships
controller/; CA-META-004 added to demo Constitution. Open: one-shot dispute enforcement in
code (on-dispute.yml is an unbounded re-dispatch trigger today; rounds bound it, per-finding
one-shot does not exist yet); zh README + faq two revisions behind; ratchet N/M thresholds
unbound.
