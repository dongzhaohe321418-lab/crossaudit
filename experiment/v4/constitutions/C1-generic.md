# C1 — Broad generic Constitution

**Registered level:** C1
**Purpose:** provide explicit human-written quality concepts without making
their criteria fully mechanical. C1 is concept-, order-, rule-ID-, and severity-
matched to C2. Differences in C2 sharpen decidability; they do not add topics.

`BLOCKER` gates the registered artefact. `ADVISORY` is recorded and never gates.
Every finding cites exactly one rule below, identifies a location, and explains
the evidence. Passed checks are not findings. Arithmetic that a deterministic
tool can settle is referred rather than decided from mental calculation.

## CA-TASK-001 — Fulfil the stated task

- **Severity:** BLOCKER
- **Applies to:** the task specification and the complete artefact bundle
- **Criterion:** The artefact should address all important deliverables and
  constraints in the task specification. Material omissions or departures from
  the requested result are findings. Minor presentation choices and useful
  extra material should not block unless they prevent the requested use.
- **Boundary:** The auditor should distinguish an omitted requested outcome from
  a merely different but usable presentation. It should identify the request it
  believes was missed rather than treating personal preference as task scope.

## CA-EVD-001 — Support consequential claims

- **Severity:** BLOCKER
- **Applies to:** factual, scientific, and quantitative claims and their evidence
- **Criterion:** Important factual, scientific, or quantitative claims should
  have enough evidence and provenance for a competent reviewer to check them.
  Unsupported consequential claims are findings; ordinary explanatory prose
  need not be burdened with unnecessary citations.
- **Boundary:** Evidence can be a source, input, test, calculation, or committed
  artefact. The question is whether the consequential claim can actually be
  checked, not whether every sentence carries a formal citation.

## CA-DATA-001 — Represent quantities and data clearly

- **Severity:** BLOCKER
- **Applies to:** reported quantities, structured outputs, and data descriptions
- **Criterion:** Quantities should use meaningful units, labels, schemas, and
  sources. Data should not be ambiguous or misleading. A missing convention is
  blocking when it prevents a competent reviewer from interpreting or checking
  a consequential result.
- **Boundary:** A stylistic preference for one conventional unit, column name,
  or serialisation is not a blocker when the supplied representation is
  unambiguous and checkable. Consequential ambiguity is the intended target.

## CA-CONS-001 — Keep the artefact internally consistent

- **Severity:** BLOCKER
- **Applies to:** task statements, prose, tables, code, outputs, and metadata
- **Criterion:** Task statements, prose, tables, code, metadata, and outputs
  should not contradict one another on consequential facts. Formatting or
  harmless rounding differences are not contradictions. Calculated comparisons
  should be referred to deterministic verification.
- **Boundary:** A blocker requires two identifiable assertions that cannot both
  be true under the same interpretation. If conversion or computation is needed
  to establish that fact, the auditor should request the named tool check.

## CA-METH-001 — Disclose material method limits and exclusions

- **Severity:** BLOCKER
- **Applies to:** methods, inputs, exclusions, assumptions, and limitations
- **Criterion:** The artefact should describe methods, exclusions, assumptions,
  and limitations that materially affect the result. A consequential hidden
  exclusion or method mismatch is a finding; reasonable methodological taste or
  incomplete discussion is advisory.
- **Boundary:** The auditor should name how the missing disclosure could change
  interpretation of the result. It should not convert a preference for another
  method, parameter, or amount of exposition into a blocking defect.

## CA-REPRO-001 — Preserve a credible rerun path

- **Severity:** BLOCKER
- **Applies to:** code-backed and data-backed claims and their rerun materials
- **Criterion:** Code- or data-backed results should provide a credible way to
  identify inputs, code, environment, and rerun procedure. Missing detail is
  blocking when it prevents reconstruction of a consequential result; quality-
  of-life improvements are advisory.
- **Boundary:** Reproduction need not be effortless or use the auditor's
  preferred tooling. The blocking question is whether the supplied record
  identifies the actual materials and procedure well enough to reconstruct it.

## CA-META-001 — Treat missing required evidence explicitly

- **Severity:** BLOCKER
- **Applies to:** evidence needed to evaluate an applicable rule above
- **Criterion:** When evidence needed to apply one of the rules above is absent
  or unreadable, report that absence rather than assuming compliance. Do not
  demand evidence the task and rules do not actually require.
- **Boundary:** Missing evidence is not a licence to invent what it would have
  shown. The auditor names the absent item and the rule that made it necessary,
  while requests outside those rules remain non-blocking suggestions.

## CA-META-002 — Keep audit allegations grounded

- **Severity:** BLOCKER for audit integrity
- **Applies to:** the structure and evidence of the audit reply itself
- **Criterion:** A blocking allegation should cite an applicable rule, concrete
  artefact evidence, and the affected location. Uncertainty, preference, or a
  question for a tool is not by itself a blocker and should be recorded in the
  appropriate non-finding field.
- **Boundary:** Passed checks belong in `checks_performed`, tool questions in
  `referred_to_tools`, and unresolved evidential limits in the escalation field.
  None becomes a defect merely because the auditor spent effort on it.
