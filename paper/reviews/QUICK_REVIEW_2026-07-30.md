# Quick Pre-Submission Check

**Paper**: CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic Science
**Authors**: Zhaohe Dong
**Date**: 2026-07-30
**Skills applied**: `review-paper-light` (Claes Bäckman, 2-agent protocol) + frameworks from `paper-review` (lcrawfurd: Edmans / Humphreys dimensions)

---

## Overall Assessment

The paper names a timely structural problem (same-source supervision of agentic science), specifies an adoptable six-invariant protocol with an unusually honest threat model, and is rated **Significant** by Agent A. The single most pressing issue: the paper's own exhibit undercuts its headline claims — the conclusion asserts "the repositories are public" while §4.2 states the deployment's science repository is private, and the deployed auditor (tool-bearing Codex CLI) violates the toolless-auditor property that §5's prompt-injection defence rests on.

**Preliminary Recommendation**: Revise before sending to referees.

---

## 1. Contribution & Credibility (Agent A)

### Part 1 — Central Contribution

**One-sentence claim (authors' framing).** CrossAudit is a lightweight, infrastructure-minimal, git-native protocol under which every increment of machine-generated research is audited by an agent from a different model vendor against a versioned human-authored rulebook, with deterministic checks running first, a bounded revision loop, and human oversight only by escalation — yielding a replayable, third-party-auditable supervision ledger, specified as six invariants, implemented in GitHub Actions plus a few hundred lines of Python, and running live in the author's computational-chemistry pipeline.

**Contribution type(s).** New question/problem framing (the "same-source supervision problem"); new method/protocol (primary); new setting (LLM-judge bias results + CI practice transplanted to research supervision). Not new data — no corpus, benchmark, or released ledger statistics.

**Closest prior works (from the paper's own bibliography).**
1. *AI Scientist family* (lu2024aiscientist, yamada2025aisv2, lu2026nature): supervision there is an internal automated reviewer with its trace inside the platform; CrossAudit adds an externalized, cross-vendor audit whose entire history is a versioned artifact, vendor-neutrally specified.
2. *AI co-scientist* (gottweis2025coscientist): critique is same-vendor internal reflection/tournament; CrossAudit adds hard vendor heterogeneity (I1), a non-overridable model-free check layer (I4), and a bounded escalation boundary (I5–I6).
3. *panickssery2024* (with zheng2023): establishes self-preference in LLM evaluators; CrossAudit operationalizes the remedy architecturally but delivers no test of whether cross-vendor pairing improves defect detection — the empirical premise is inherited entirely by citation.

`[UNVERIFIED — authors must confirm]` The bibliography contains nothing on multi-agent debate/critique as oversight, provenance/tamper-evident record-keeping, or open peer review — adjacent literatures. Cite and differentiate, or state why not.

**Does the framing overstate?** Mostly calibrated, three exceptions: (1) Contribution 3 promises the reference implementation "and its live deployment", but §4.2 describes a materially different system than the released artifact; (2) I1's "removes self-preference bias by construction ... decorrelates vendor-idiosyncratic failure modes" — the second half is asserted, not evidenced; (3) the conclusion's "the repositories are public" collides with §4.2's "private science repository".

**Rating: Significant.** Timely framing, adoptable synthesis, honest threat model; short of transformative because every component is a known mechanism recombined and the paper offers zero quantitative evidence, not even descriptive statistics from its own running ledger.

### Part 2 — Credibility of Core Claims

**Decorrelated review (I1): partially delivered.** Cross-vendor pairing genuinely eliminates self-evaluation, but "decorrelated" is a claim about the joint error distribution and no evidence is offered — no disagreement rates, no seeded-defect comparison. I1 also oscillates between "vendor" and "model family" without defining either, and is enforced by reading a config string the operator wrote.

**Replayable history (I2, I3): delivered for the record, not for the verdicts.** (a) LLM verdicts are not re-derivable (model version/prompt/sampling pinning unspecified); (b) the deployment's controller state "deliberately lives outside both repositories" — in tension with I2's "replayable by a third party from the repositories alone"; (c) the one live deployment's science repo is private, so third-party inspectability is demonstrated nowhere. "Tamper-evident" is a policy assertion absent signing/branch-protection/anchoring.

**Bounded interruption (I5, I6): delivered per increment, unevidenced in aggregate.** The O(increments)→O(escalations) claim depends on the escalation rate, never reported; I3 converts auditor flakiness directly into human interruptions.

**Assertion vs. mechanism inventory.** Mechanism-backed: DCL precedence, two-repo separation, schema-validated replies, per-increment termination. Assertion-backed: vendor decorrelation; audit-branch immutability; tamper evidence; "runs unattended"; "costs cents"; CA-META-003 enforcement (as written, a well-formed *fabricated* rule citation would pass); "close to the minimum".

**Seminar skeptic:** "You have a running system and report no numbers from it. Your only deployment is your own, private, and doesn't match the artifact you released. And the one cheap experiment supporting your central invariant — same-vendor vs. cross-vendor on seeded defects — was never run."

### Part 3 — Required Analyses / Additions

1. **[CRITICAL] Descriptive statistics from the live ledger** (increments, verdict distribution, rounds, disputes, escalations, latency, cost). Absence leaves "runs unattended"/"costs cents"/attention-economics unevidenced and contradicts the ledger-as-data thesis.
2. **[CRITICAL] Minimal heterogeneity experiment** — seeded-defect recall for cross- vs. same-vendor pairings, or at minimum cross-model verdict-disagreement statistics. I1 currently rests on transferred citations about a different setting.
3. **[CRITICAL] Invariant-by-invariant compliance table for the deployment** reconciling divergences (tool-bearing auditor; controller state vs. I2; private repo vs. public replayability; immutability enforcement). Under the paper's own "exactly when" definition the deployment's CrossAudit status is undemonstrated.
4. **[CRITICAL] Precise replayability/tamper-evidence spec**: what is pinned in the ledger; replay-of-record vs. reproduction-of-verdict; the mechanism behind "tamper-evident" or retract the regulated-settings claim.
5. **[CRITICAL] Exhibit the Constitution**: at least one complete rule + the meta-rules verbatim; state whether the runner resolves cited rule IDs against the pinned Constitution (closing the fabricated-citation hole in I3).

### Part 4 — Questions to the Authors

1. Invariant by invariant, is the §4.2 deployment CrossAudit-compliant under §3.2's "exactly when" — and if not, what does the existence proof prove?
2. Which repositories can a reader replay today, given "the repositories are public" (conclusion) vs. the private science repo (§4.2)?
3. What are the aggregate deployment statistics, and does the O(escalations) claim survive the escalation rate implied by I3's convert-failure-to-ESCALATE rule?
4. Does the runner verify cited rule IDs against the Constitution at the cited hash, in code — or does schema validation alone let a fabricated citation pass?
5. What evidence supports "decorrelates vendor-idiosyncratic failure modes", and how is I1 verified at all behind OpenAI-compatible endpoints?

### Part 5 — Preliminary Recommendation

**Revise before sending to referees.** Timely and plausibly publishable; but internal inconsistencies (public vs. private, deployment vs. specification, I2 vs. controller state) and the absence of free descriptive ledger statistics are defects fixable in weeks that referees would unanimously flag.

### Exposition Notes

- Contribution articulated early and well; abstract substance dominates appropriately but the (i)–(iii) sentence should be split.
- §3.3 discusses decidability without showing a rule (add an example/appendix); §4.2 is a wall-of-prose describing the paper's only empirical object — restructure around a compliance table.
- §6 redundancy: "ledger buys science socially" and "ledger as data asset" repeat the failed-audits-are-data point; merge.
- Terminology drift: "vendor" vs. "model family" never reconciled — define the equivalence class once.
- Trim empirical-sounding flourishes ("cheapest layer of assurance computational science has ever been offered").
- Figure 1 earns its space. §5 is the paper's best section — pointer to it belongs in §1.

---

## 2. Overclaiming & Unsupported Claims (Agent B)

### Effectiveness Overclaiming

1. **[CRITICAL] §3.2 I1** | "removes self-preference bias by construction ... and decorrelates vendor-idiosyncratic failure modes" | Cited evidence covers self-recognition when judging one's own outputs; "decorrelates" is an untested empirical prediction (deferred by §4.3 itself). | Fix: "removes the demonstrated self-evaluation channel of self-preference bias and is designed to decorrelate vendor-idiosyncratic failure modes (unmeasured here; §4.3)."
2. **[MAJOR] §2** | "removes the sharpest known bias (self-preference) and decorrelates..." | Same double overclaim + unsupported superlative. | Fix: "avoids the best-documented bias in this setting; intended to decorrelate."
3. **[MAJOR] §1** | "applied by an agent with no stake ... preserved verbatim in a public ledger" | Vendor identity is self-declared config; "no stake" unargued; deployment ledger partly private. | Fix: scope to "a declared second-vendor agent ... (public where the repositories are public)."
4. **[MAJOR] §3.1** | "neither agent can alter the other's record even in error" | Holds only under unverified platform permissions; silent on self-rewriting absent branch protection. | Fix: credentials phrasing + branch-protection caveat.
5. **[MAJOR] §4.1** | "most common failure shape ... made harmless" | "Most common" uncited; escalation isn't harmless (spends the binding resource). | Fix: "a common failure shape ... converted from silent passage into an escalation."
6. **[MAJOR] §4.2** | "immutable per-cycle directory ... may never rewrite" | Policy, not enforced property; name the mechanism. | Fix: "append-only by policy, enforced by controller validation of every audit commit."
7. **[MAJOR] §4.2** | "neither agent can tamper with the record of its own supervision" | Externalized controller state buys detectability, not impossibility. | Fix: "tampering ... is detectable against controller-held state."
8. **[MAJOR] §4.2** | "any single component can fail without loss of state" | Untested fault-tolerance guarantee; controller-host failure plausibly loses exactly the externalized state. | Fix: "designed so that ... without loss of ledger state."
9. **[MAJOR] §5** | "Collusion ... excluded by architecture" | Committed artifacts are a channel; coordination is inspectable, not impossible. | Fix: "Collusion has no covert channel."
10. **[MAJOR] §5** | "irreducible by adding more LLM auditors, however many" | Impossibility claim without proof; corpora overlap but are not identical. | Fix: "cannot be assumed reducible."
11. **[MAJOR] §6** | "None of this requires new infrastructure ... which is what the protocol guarantees" | Institutional change ≠ artifact existence; "guarantees" only under faithful implementation. | Fix: drop "guarantees"; "new technical infrastructure."

### Mechanism Claims Stated as Facts

1. **[MAJOR] §1** | "Two agents that share a training distribution share blind spots, and a reviewer that shares the author's blind spots approves precisely the author's characteristic errors." | Core motivating mechanism is a hypothesis; cited evidence covers same-model self-evaluation only. | Fix: "plausibly share ... risks approving."
2. **[MAJOR] §2** | "the mechanism generalises: models sharing a training pipeline share stylistic priors and knowledge gaps" | Names the evidence gap then leaps it in the indicative. | Fix: "we hypothesise the mechanism generalises ... are likely to share."
3. **[MAJOR] §3.2 post-I6** | "Every additional level invites severity-inflation negotiation" | Behavioral law asserted from zero observations. | Fix: mark as design judgement.
4. **[MAJOR] §3.2 I4** | "the only supervision layer with failure modes fully independent of every model" | DCL scripts were LLM-assisted (Acknowledgements) — not "fully independent". | Fix: "least entangled".
5. **[MINOR] §3.2 I5** | oscillation "can ... indefinitely" presented as known failure mode | Hedge or report an instance.
6. **[MINOR] §3.3** | "the Auditor cannot exceed the rules ... the Generator will learn" | ADVISORY findings and CA-META-004 escalations do exceed enumerated rules; "will learn" unevidenced. | Fix: "blocking power cannot exceed ... is free to exploit."
7. **[MINOR] §3.4** | "prevents the dispute channel from becoming the oscillation" | Boundedness is the defensible claim. | Fix accordingly.
8. **[MINOR] §2** | "Software engineering solved an analogous trust problem" | "Addressed."

### Generalization Beyond the Evidence

1. **[MAJOR] Abstract + §2** | "Across all of these ... same model family" | Likely factually wrong for AI Scientist v1 (GPT-4o reviewer with Claude generators reported). Defensible shared property: internal, operator-chosen, no heterogeneity commitment. | Fix: verify every cited pairing; soften.
2. **[MAJOR] §4.3** | existence proof scope | n=1, self-reported, variant-of-spec; report basic statistics and scope the claim to the deployed variant.
3. **[MAJOR] §6** | "generalises ... to any agentic work product" | Untested conjecture from one self-deployment. | Fix: "should in principle extend ... a conjecture we have not tested."
4. **[MAJOR] §6** | regulated-settings fit | Data-integrity regimes demand validated systems and enforced immutability, undemonstrated. | Fix: "no claim of compliance with any specific regime."
5. **[MAJOR] §1+§6** | CI analogy load-bearing ("the analogy is exact") | Uncited causal history; deterministic-tests vs. stochastic-judge disanalogy never weighed. | Fix: hedge and acknowledge the disanalogy.
6. **[MAJOR] §6** | "would cost little to re-instantiate across vendor lines" | Other organizations' procurement/confidentiality costs not ours to estimate.
7. **[MINOR] §1** | "most agentic systems" | Two examples. | Fix: "the prominent systems above."
8. **[MINOR] §6** | "an afternoon" | Plumbing only; the Constitution is the real authoring cost.

### Missing Caveats

1. **[MAJOR] Cost claims** — multi-round amplification, Constitution tokens per call, CI minutes on private repos, escalation-handling human time. Scope: "at mid-2026 API prices, per audit call, excluding escalation time."
2. **[MAJOR] No reported LLM-layer catch** — the six-minute BLOCK is DCL-attributable; say so explicitly and state whether any LLM-layer findings are claimed.
3. **[MAJOR] Vendor identity self-declared** — the ledger proves the exchange, not the identity of models behind endpoints; add §5 bullet.
4. **[MAJOR] Prompt-injection defence local overstatement** — "strictly as data" is a convention; forward-reference §5's residual in the same sentence.
5. **[MAJOR] Attention economics unmeasured** — conditional on low escalation/advisory volumes; observed informally, not measured.
6. **[MAJOR] Constitution dependence** — all downstream assurance bounded by an unvalidated rulebook; the one deployed policy is private; publish or excerpt.
7. **[MAJOR] Confidentiality of cross-vendor calls** — shipping unpublished research to a second vendor's API: IP/DPA/disclosure risk unmentioned; add §5 scope bullet.
8. **[MAJOR] "Replayable" ≠ re-executable** — record re-inspection vs. verdict reproduction; define once.

### Priority/Novelty Assertions

1. **[MAJOR] §6** "field currently lacks entirely" → "largely lacks" (partial counterexamples plausible).
2. **[MAJOR] §4.3** "cheapest layer of assurance computational science has ever been offered" → unverifiable superlative; unit tests/checksums are also ~free.
3. **[MAJOR] §2** "sharpest known bias" → "best-documented in this setting."
4. **[MAJOR] Conclusion** "close to the minimum" → add per-invariant necessity arguments or drop.
5. **[MAJOR] §1–2** implicit novelty of heterogeneous judging → prior art on diverse judge panels exists; scope novelty to protocol-plus-ledger packaging.
6. **[MINOR] Abstract** "usually lives in opaque platform logs" → "in the systems above."

### Internal Consistency

1. **[CRITICAL] Conclusion "the repositories are public" vs. §4.2 "private science repository"** — the thesis is third-party inspectability; the sole deployment cannot be inspected. Fix: state precisely which repositories are public; qualify every "public ledger" claim.
2. **[CRITICAL] §4.1/§5 toolless auditor vs. §4.2 Codex-CLI auditor** — the deployment violates the property offered as the injection defence. Fix: extend the threat model to tool-bearing auditors with the deployment's actual containment, or present the divergence explicitly.
3. **[MAJOR] I2 vs. §4.2 controller state outside repositories** — not all three sentences can be true; classify controller state and reconcile.
4. **[MAJOR] §3.2 "exactly when" vs. §4.3 existence proof** — map the deployment onto all six invariants or scope the claim to a variant.
5. **[MAJOR] §6 O(escalations) vs. per-increment advisory reading** — the elaboration contradicts the headline complexity.
6. **[MINOR] Two severities vs. endorsed scope-granular blocking** — say why scopes don't reopen the negotiation surface severities would.
7. **[MINOR] I4 "fully independent" vs. LLM-assisted DCL authorship.**
8. **[MINOR] "Humans interrupted only by ESCALATE" vs. deployment's standing PI approval gate.**

---

## Priority Action Items

**CRITICAL** (could cause desk rejection or major objections):
1. Resolve public/private repository contradiction everywhere (B-IC1; A-Q2).
2. Reconcile toolless-auditor spec with the tool-bearing deployed auditor, in the threat model (B-IC2; A-Q1).
3. Soften I1's "removes ... by construction / decorrelates" to mechanism-scoped claims (B-E1).
4. Report descriptive ledger statistics, or scope every "runs unattended / costs cents" claim (A-R1).
5. Run or explicitly defer the same-vendor vs. cross-vendor comparison; stop banking "decorrelated" in abstract/conclusion (A-R2).
6. Add deployment-vs-invariants compliance mapping (A-R3).
7. Specify replayability precisely; name the tamper-evidence mechanism or retract (A-R4).
8. Exhibit at least one Constitution rule + close the fabricated-citation hole in I3 (A-R5).

**MAJOR** (will likely be raised by referees): items B-E2..E11, B-M1..M4, B-G1..G6, B-C1..C8, B-P1..P5, B-IC3..IC5, plus exposition restructuring of §4.2 and §6 merge.

**MINOR** (polish): B-M5..M8, B-G7..G8, B-P6, B-IC6..IC8; abstract sentence-splitting; terminology unification ("vendor" vs. "model family").

---

*Generated with the `review-paper-light` skill (Claes Bäckman) and `paper-review` frameworks (lcrawfurd), run as a 2-agent parallel review.*
