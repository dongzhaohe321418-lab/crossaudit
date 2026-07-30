# Cross-vendor audit of this repository — decision: BLOCK (accepted)

**Provenance.** Second-vendor audit of the repository and paper v4, relayed by the
operator on 2026-07-30, baseline commit `bb13da2`. Committed verbatim in spirit
(operator-relayed summary) as a ledger artefact. The generator (Claude-based agent that
authored this repository and paper) has reviewed every finding and responds below.
This file is the dispute/acceptance record required by the protocol's own round rules.

## Findings and dispositions

| # | Finding (auditor) | Disposition |
|---|---|---|
| P0-1 | "Sealed / pre-registered" did not hold: `experiment/defect_key.json` was public from registration commit `216bdc9` (a mis-pathed `.gitignore`), and is in any case derivable from the public deterministic generator. | **ACCEPTED.** Verified in history. "Sealed/blinded" claims withdrawn everywhere; procedural blinding of the fresh-context subagents remains asserted but is not ledger-verifiable. |
| P0-2 | 43/43 depends on post-outputs scoring-map expansion; the frozen map yields 38/43. | **ACCEPTED.** Independent recomputation reproduced (38/43 frozen; 43/43 adjudicated). Scorer now reports both maps; the paper reports 38/43 as the frozen score and the adjudication as exploratory. |
| P0-3 | "Entire designed scope, none outside it" for the DCL contradicts the registered taxonomy (L6 was registered LLM-only; DCL caught it 5/5). | **ACCEPTED.** L6's flag component was misregistered. Paper now reports DCL = 12/12 on registered D-scope plus 5/5 cross-hits on L6, with the misregistration named. |
| P0-4 | Not an end-to-end reference-implementation run (no dispatch/DCL-first pipeline; subagent arm ≠ frozen runner; session sampling). | **ACCEPTED.** Re-described as a component-level model-review trial on the reference format and Constitution. "End-to-end harness" withdrawn. |
| P0-5 | Pilot raw outputs themselves violate I3 (no Constitution commit hash; runner does not validate citations). | **ACCEPTED.** Noted in the paper; runner to record constitution hash and validate citations in the rerun. |
| §1 | Reference-skeleton enforcement gaps: validator accepts empty/fabricated-rule PASS; Generator-controlled round trailer; dispatch-payload-trusted scope; unverified callbacks; offline PASS path. Proposed invariants I7 (coverage/receipt binding) and I8 (fail-closed admission). | **ACCEPTED as protocol work.** The skeleton is transport, not enforcement; the paper's next revision adopts I7/I8 and the deployment checklist. Spec ambiguity between I3 and I4 on (DCL fail + invalid report) resolved: DCL verdict dominates, auditor failure additionally escalates. |
| §3.1–3.5 | Scoring not per-defect-bound; "zero false-alarm" overstated (0 BLOCKER FPs, but 5 ADVISORY findings across 5/10 clean increments; 0/10 ⇒ one-sided 95% upper bound ≈26%); severity discipline untested (no L3-only control); checklist-aligned prompt/corpus coupling; arm execution provenance self-attested. | **ACCEPTED.** All now stated in the paper's caveats. |

## Meta

The auditor's overall verdict — "a promising protocol draft and audit-record prototype,
plus a synthetic component study that must be reported as exploratory" — is adopted as
the paper's own self-description. This audit, performed by a second-vendor agent against
the generating agent's work and reproduced to the digit by re-scoring, is the strongest
demonstration of the protocol's thesis available in this repository.
