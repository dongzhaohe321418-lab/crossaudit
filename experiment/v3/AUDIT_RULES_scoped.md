# Audit Constitution

> Template. Replace bracketed text, keep rule IDs stable, and version every change
> with a commit message explaining why. Format spec: `docs/audit-rules-spec.md`.

**Scope:** all experiment increments under `experiments/` of `[owner/science-repo]`.
**Severity levels:** `BLOCKER` gates the pipeline; `ADVISORY` is recorded only.
**Reports must cite:** rule IDs + the commit hash of this file they applied (invariant I3).

---

## Section DATA — data integrity


> Scoped for the v3 study. Six rules of the deployment Constitution are out
> of scope; `experiment/v3/AUDIT_RULES_v3-study.md` says which and why.


### CA-DATA-001 — Every reported quantity carries units and provenance
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/results.json`
- **Criterion:** Each numeric entry has non-empty `unit` and `source` (script + commit, or dataset/instrument identifier). Decidable from the file alone.
- **Rationale:** A number without units and origin cannot be checked by anyone, now or later.

### CA-DATA-002 — Results and metadata must not contradict
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** Quantities, methods, and sample identifiers stated in `metadata.yml` match those in `results.json` and in any prose summary. Any mismatch is a finding.
- **Rationale:** Internal contradiction is the cheapest reliable signal of a pipeline defect.

### CA-DATA-003 — No silent data exclusion
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** If an increment drops data points, runs, or configurations relative to its declared inputs, the exclusion and its reason are stated in `metadata.yml` (`exclusions:` list).
- **Rationale:** Undisclosed exclusion is the classic path from noise to false discovery.

## Section METH — methodology floor

### CA-METH-002 — Convergence criteria stated and met
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/results.json`
- **Criterion:** `convergence.converged == true`, and threshold + achieved value are both present. (The DCL checks the flag mechanically; this rule covers agreement between logs and declared values.)
- **Rationale:** Unconverged numbers are not results.

### CA-REPRO-001 — Increment is self-describing
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** `metadata.yml` includes: objective (1–3 sentences), inputs (paths/identifiers), method block, code version (commit hash), environment (container tag or dependency lockfile reference).
- **Rationale:** The unit of science here is the increment; each must stand alone.

### CA-REPRO-002 — Rerun path exists
- **Severity:** ADVISORY
- **Applies to:** `experiments/**/`
- **Criterion:** A `rerun:` entry (command or job script reference) exists and its referenced files are committed.
- **Rationale:** Reproducibility that requires archaeology is not reproducibility.

## Section DOM — domain rules ([replace: computational chemistry examples])

### CA-META-001 — Missing evidence is a finding, not a pass
- **Severity:** BLOCKER
- **Applies to:** audit process
- **Criterion:** Where a rule's required artifact is absent or unreadable, the Auditor reports that as a finding under this rule — never infers compliance.
- **Rationale:** Silence must not launder defects.

### CA-META-002 — Report validity
- **Severity:** BLOCKER
- **Applies to:** audit process
- **Criterion:** A report lacking rule-ID citations, the Constitution hash, or the per-section checklist is invalid; the pipeline treats it as `ESCALATE`.
- **Rationale:** Invariant I3; guards against degenerate/hallucinated reports.

### CA-NUM-001 — Arithmetic belongs to the deterministic channel
- **Severity:** ADVISORY
- **Applies to:** any finding asserting that two numbers disagree
- **Criterion:** the finding states the tolerance under which they disagree, and that tolerance is at least the printed precision of both numbers. Where establishing the disagreement requires arithmetic — a unit conversion, a sum, a ratio — the Auditor reports the pair as *requiring tool verification* and does not raise a BLOCKER on the strength of a calculation it performed itself. A finding asserting a numerical disagreement the Auditor computed, without a deterministic check confirming it, is invalid under CA-META-002.
- **Rationale:** measured, not supposed. Across five clean increments the Auditor stated the correct conversion constant, read the correct inputs, and misevaluated the product by up to 1.8e-3 eV while adjudicating a discrepancy of 8.8e-5 eV — an error twenty times the size of the question. Its verdict tracked its own arithmetic error rather than the data: the two increments it declared contradictory were the two where it multiplied worst. The earlier version of this rule required the Auditor to perform the conversion and state a tolerance; it did both, and was still wrong, because the defect was never omission. This is invariant I4 arriving as evidence: a comparison a script settles exactly must not be settled by a model.

