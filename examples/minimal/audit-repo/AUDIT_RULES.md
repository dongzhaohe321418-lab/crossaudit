# Audit Constitution (demo)

> Compact demo Constitution for the minimal example. For a real deployment,
> start from `templates/AUDIT_RULES.md` in the main CrossAudit repository and
> grow your own — especially the DOM section. Format: `docs/audit-rules-spec.md`.

**Severity:** `BLOCKER` gates; `ADVISORY` records. Reports must cite rule IDs
and this file's commit hash (I3).

### CA-DATA-001 — Every reported quantity carries units and provenance
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/results.json`
- **Criterion:** each numeric entry has non-empty `unit` and `source`.
- **Rationale:** a number without units and origin cannot be checked by anyone.

### CA-DATA-002 — Results and metadata must not contradict
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** quantities, methods and identifiers in `metadata.yml` match
  `results.json` and any prose in the increment.
- **Rationale:** internal contradiction is the cheapest reliable defect signal.

### CA-METH-002 — Convergence criteria stated and met
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/results.json`
- **Criterion:** `convergence.converged == true` with threshold and achieved
  value present and consistent with any logs in the increment.
- **Rationale:** unconverged numbers are not results.

### CA-REPRO-001 — Increment is self-describing
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** `metadata.yml` states objective, inputs, method, code_version,
  environment.
- **Rationale:** each increment must stand alone.

### CA-META-001 — Missing evidence is a finding, not a pass
- **Severity:** BLOCKER
- **Applies to:** audit process
- **Criterion:** absent/unreadable required artifacts are reported as findings;
  compliance is never inferred.
- **Rationale:** silence must not launder defects.

### CA-META-002 — Report validity
- **Severity:** BLOCKER
- **Applies to:** audit process
- **Criterion:** a report without rule citations + Constitution hash is invalid
  → treated as ESCALATE.
- **Rationale:** guards against degenerate reports (invariant I3).

### CA-META-003 — The Auditor does not legislate taste
- **Severity:** BLOCKER (for the Auditor's conduct)
- **Applies to:** audit process
- **Criterion:** no BLOCKER finding without citing a BLOCKER-severity rule;
  uncovered judgement calls are ADVISORY at most.
- **Rationale:** keeps the gate objective and disputes resolvable.

### CA-META-004 — Escalate on competence boundary
- **Severity:** — (procedural)
- **Applies to:** audit process
- **Criterion:** if deciding a finding requires information outside the increment plus
  Constitution, return ESCALATE with the specific question for the human.
- **Rationale:** knowing when not to decide is part of the audit.
