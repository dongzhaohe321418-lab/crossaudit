# Audit Constitution

> Template. Replace bracketed text, keep rule IDs stable, and version every change
> with a commit message explaining why. Format spec: `docs/audit-rules-spec.md`.

**Scope:** all experiment increments under `experiments/` of `[owner/science-repo]`.
**Severity levels:** `BLOCKER` gates the pipeline; `ADVISORY` is recorded only.
**Reports must cite:** rule IDs + the commit hash of this file they applied (invariant I3).

---

## Section DATA — data integrity

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

### CA-METH-001 — Declared method matches executed method
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** Method parameters in `metadata.yml` (e.g. `[functional, basis set, convergence thresholds]`) match those in the run inputs/logs committed with the increment.
- **Rationale:** "Wrote B3LYP, ran PBE" invalidates every downstream claim.

### CA-METH-002 — Convergence criteria stated and met
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/results.json`
- **Criterion:** `convergence.converged == true`, and threshold + achieved value are both present. (The DCL checks the flag mechanically; this rule covers agreement between logs and declared values.)
- **Rationale:** Unconverged numbers are not results.

### CA-METH-003 — Parameter choices within community norms
- **Severity:** ADVISORY
- **Applies to:** `experiments/**/metadata.yml`
- **Criterion:** Flag parameter choices outside `[state your field's accepted ranges, with citations]`, with a one-line reason why they may matter.
- **Rationale:** Taste, not law — hence advisory (see CA-META-003).

## Section REPRO — reproducibility

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

### CA-DOM-001 — Energies comparable only at matching theory level
- **Severity:** BLOCKER
- **Applies to:** `experiments/**/`
- **Criterion:** Any energy difference or ranking in the increment compares values computed with identical functional/basis/corrections, or explicitly labels the mismatch.
- **Rationale:** Cross-level comparisons are the field's most common silent error.

### CA-DOM-002 — Geometry provenance for derived properties
- **Severity:** ADVISORY
- **Applies to:** `experiments/**/`
- **Criterion:** Properties computed on a geometry state which optimisation produced it (level, convergence).
- **Rationale:** Property claims inherit geometry errors invisibly.

> [Add your own CA-DOM rules here — aim for ten decidable ones before first deployment.]

## Section META — rules about the audit itself

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

### CA-META-003 — The Auditor does not legislate taste
- **Severity:** BLOCKER (for the Auditor's conduct)
- **Applies to:** audit process
- **Criterion:** Matters of scientific judgement not covered by a decidable rule are reported as `ADVISORY` at most. The Auditor never issues a `BLOCKER` without citing a BLOCKER-severity rule.
- **Rationale:** Keeps the gate objective; keeps disputes resolvable.

### CA-META-004 — Escalate on competence boundary
- **Severity:** — (procedural)
- **Applies to:** audit process
- **Criterion:** If deciding a finding requires information outside the increment + Constitution (private context, unstated intent, external facts the Auditor cannot verify), return `ESCALATE` with the specific question for the human.
- **Rationale:** Knowing when not to decide is part of the audit.
