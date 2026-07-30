# FAQ

**Q: Why two repositories instead of one?**
Separation of powers, mechanically enforced. The Auditor has no write access to the Science Repo, the Generator none to the Audit Repo. In a single repo, branch protection can approximate this, but the failure modes (a mis-scoped token, a force push) are quieter. Two repos make the boundary a permission, not a convention. It also gives the audit trail its own star-able, citable home.

**Q: Isn't this expensive? Every push triggers an LLM audit.**
The deterministic layer is free and catches the embarrassing majority of hard defects. LLM audit cost scales with increment size, not compute size — auditing a 200-line results increment is cents, while the experiment behind it may have burned HPC hours. Supervision at ~1% of compute cost is historically cheap. You can also batch: audit on PR rather than on push.

**Q: Why not three or more auditors and majority voting?**
You can — the protocol composes. But each added vendor adds cost and latency for sharply diminishing decorrelation (all frontier models share most of their corpus). The CrossAudit position: spend that budget on better deterministic checks and a sharper Constitution first; add a second auditor only for increments tagged high-stakes.

**Q: What if the Auditor hallucinates a finding?**
That is what disputes are for (architecture §5): the Generator contests by rule ID, the Auditor withdraws or upholds, upheld disputes at the round bound go to the human. Invariant I3 also voids reports that cite no rules — the most common hallucination shape.

**Q: Can the Generator and Auditor collude?**
They never share context — communication is exclusively through committed artifacts (reports, disputes), which the human can read. "Collusion" would have to happen in public, in the ledger. The realistic risk is softer: convergent style over many rounds. The Constitution review cadence and the escalation record are the counterweight.

**Q: Does this replace peer review?**
No. It is *pre*-review: continuous, mechanical-plus-model supervision that makes each increment audit-clean before any human sees it. Think of it as CI for scientific claims. Human peer review moves up a level: reviewing the Constitution, the escalations, and the science.

**Q: My field can't write decidable rules.**
Read architecture §9's litmus test. Often "can't" means "haven't yet" — provenance, units, schema, and internal consistency are decidable in every quantitative field. But if your quality judgement is irreducibly holistic, CrossAudit degrades gracefully to I1 alone; just know that is what you are running.

**Q: Why git specifically?**
Nothing in the invariants requires git — they require an append-only, diffable, third-party-replayable ledger with versioned rules. Git is simply the one such ledger every researcher already has, with hosting, permissions, CI hooks, and issues attached.
