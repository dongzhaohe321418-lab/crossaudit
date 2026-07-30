# Quick Pre-Submission Check — v2 (post-revision re-review)

**Paper**: CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic Science (rev. bb4879c + related-work expansion)
**Date**: 2026-07-30 · Protocol: `review-paper-light` 2-agent parallel, fresh agents, no access to v1 report

---

## Overall Assessment

Claim discipline improved sharply: Agent B reports **zero CRITICAL** (v1: 3), explicitly noting "unusually good claim discipline" and verifying the newly added related-work distinctions (PoLL, Kosmos, statcheck/PPS, Constitutional AI) as accurate and non-strawmanned. Agent A rates the contribution **Significant** and confirms the four promised contributions are delivered where promised. Remaining weight is now on the **evidence layer**: the distinctive cross-vendor LLM layer has no reported catch, no operational telemetry, and the flagship ledger is private — "a paper about auditable ledgers whose flagship ledger cannot be audited is a structural irony referees will not forgive."

**Preliminary Recommendation** (Agent A, verbatim): Revise before sending to referees.

---

## Agent A (Contribution & Credibility) — key findings

- Rating: **Significant**. Synthesis is a genuine protocol, not a workflow suggestion; evidence-light but self-aware.
- Related-work now adequate; two seams: Curie differentiation is asserted in one clause; bloxberg dismissal never engages external anchoring — the exact gap in the paper's own threat model.
- Sharpest observation: "structural independence" is credential-level only — one principal authors the Constitution, prompts both agents, controls publication; auditor system prompt is not a ledger artefact.
- I2 wrinkle: escalations live in issues = platform state, so "repositories alone" is not strictly true even of the reference design.
- Weakest load-bearing claim: nothing yet distinguishes the deployed system from "deterministic checks plus logging with an expensive stochastic bystander."

**[CRITICAL] required additions (unchanged in kind from v1, sharpened):**
1. Minimal seeded-defect pilot (20–50 defects, hetero- vs homogeneous pairing) on the authors' own pipeline.
2. Operational telemetry table (cycles, verdicts, rounds, escalations, advisories, cost).
3. Public (redacted) mirror of a handful of complete audit cycles.
4. Operator-level threat entry (selective publication, pre-publication rewriting, audit re-rolling) + anchoring mechanism or explicit re-scoping of "third-party-auditable".
5. Threat-model reconciliation for the tool-bearing deployed auditor + ledgered change control for DCL scripts and auditor prompt.

Pointed questions center on: what can the CLI auditor execute; would a PASS-stub auditor have produced a different history; who controls DCL scripts; what exactly can a third party verify; which of definition/§4.2-claim/deployment gets amended.

Exposition: split §2 first paragraph at "The pattern persists"; merge Discussion's duplicated failed-audits-are-data point; table-ify §4.2; split abstract sentence two; artefact/artifact spelling; drop "the irony is intended"; em-dash density.

## Agent B (Claim Discipline v2) — all findings (no CRITICAL)

Effectiveness [4]: I1 "removes ... by construction" still too strong (structurally precludes only the literal self-judging configuration) [MAJOR]; collusion "no covert channel" overclaims vs steganographic coordination + tool-bearing deployed auditor [MAJOR]; "blocking power cannot exceed the rules" is rule-plus-review, not prevention [MINOR]; "forbidden to rewrite ... enforced" is detection, not prevention [MINOR].

Mechanism-as-fact [3]: §1 states as law what §2 labels hypothesis (shared blind spots) [MAJOR]; "all frontier models ingest substantially the same public literature" unverifiable, load-bearing [MINOR]; "a common failure shape" uncited [MINOR].

Generalization [4]: "runs unattended" durative with N unstated [MINOR]; "architecturally straightforward to re-instantiate" asserts internals of proprietary platforms [MINOR]; abstract universal "current frontier systems" [MINOR]; "circulates in developer tooling" from one blog post [MINOR].

Missing caveats [3]: cost paragraph reads as deployment fact but is reference-design estimate; tool-bearing auditor's token use need not scale with increment [MAJOR]; §5 injection bullet true of reference only — deployed variant forgoes the toolless defence [MAJOR]; "third-party-auditable"/"replayable" unqualified at first use [MINOR].

Novelty [3]: Kosmos parentheticals risk strawman — reframe as "no described commitment to second-party auditor or off-platform ledger" + verify quote verbatim [MAJOR]; "precisely what the community lacks" vs later "largely lacks" [MINOR]; MindStudio footnote needs access date [MINOR].

Internal consistency [5]: §4.2 opens "CrossAudit runs live" vs "exactly when" definition + declared I2 divergence — open with "A closely related variant" [MAJOR]; §1 certificate includes properties §5 says the ledger cannot prove ("no stake", who applied rules) [MAJOR]; "not the queue" vs freezing submissions [MINOR]; "no infrastructure beyond GitHub itself" vs two model endpoints [MINOR]; controller-host failure loses exactly the load-bearing off-repo state [MINOR].

Citation integrity [4]: zheng2023 cited for a prompt-injection claim it does not make [MAJOR]; "outputs resembling their own" smuggles similarity-generalization into panickssery2024 [MINOR]; "showing ... causes" upgrades evidence to fact [MINOR]; "reach peer-reviewed venues" — phrase to match what lu2026nature establishes [MINOR]. All other 12 citations verified as carrying appropriately matched claims.

---

## Priority Action Items (v2)

**Author-data-dependent (cannot be fixed by wording):** A-1 seeded pilot · A-2 telemetry (accumulates with cycles) · A-3 public mirror (author decision).

**Fixed in this revision (wording/structure):** B-E1..E4, B-M1..M3, B-G1..G4, B-C1..C3, B-P1..P3, B-IC1..IC5, B-CI1..CI4; A's operator-threat entry, DCL change-control sentence, §2 paragraph split, Discussion merge, spelling unification, acknowledgement trim, §4.2 telemetry-deferral honesty note.
