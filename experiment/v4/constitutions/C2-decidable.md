# C2 — Scoped decidable Constitution

**Registered level:** C2
**Purpose:** express the same concepts as C1 with named evidence, scope, and a
decision criterion. C2 is concept-, order-, rule-ID-, and severity-matched to
C1. The bundle schema named here must be frozen before dispatch.

`BLOCKER` gates only the affected registered artefact/action. `ADVISORY` is
recorded and never gates. Every finding cites exactly one rule, exact task or
artefact location, and observed evidence. Passed checks are not findings.
Arithmetic that a deterministic tool can settle is referred rather than decided
from mental calculation.

## CA-TASK-001 — Fulfil the stated task

- **Severity:** BLOCKER
- **Applies to:** frozen task specification and artefact manifest
- **Criterion:** For every task requirement marked `required`, the manifest
  names at least one delivered artefact and that artefact exists at the recorded
  content hash. Every explicit exact/range/format/language constraint is checked
  against its recorded value. A finding cites the failed requirement ID. Extra
  artefacts do not block unless the task explicitly forbids them or they make a
  required deliverable unusable.
- **Boundary:** Presentation preferences outside an explicit requirement remain
  advisory and cannot be converted into an inferred deliverable.

## CA-EVD-001 — Support consequential claims

- **Severity:** BLOCKER
- **Applies to:** registered consequential-claim and evidence records
- **Criterion:** Every claim marked `consequential` names at least one evidence
  ID; each ID resolves to a shipped file, source record, test, or calculation
  manifest at its recorded hash; and the evidence concerns the same claim ID.
  Missing or non-resolving evidence is a finding at that claim. Claims not marked
  consequential are outside this blocking criterion.
- **Boundary:** The rule checks evidence linkage and availability; it does not
  certify that an external source is scientifically true.

## CA-DATA-001 — Represent quantities and data clearly

- **Severity:** BLOCKER
- **Applies to:** machine-readable quantities and data manifests
- **Criterion:** Every reported numeric quantity declares a unit or explicitly
  declares `unitless: true`, a semantic name, and a source/evidence ID that
  resolves under CA-EVD-001. Every structured output validates against the
  schema named in its manifest. Unknown units, missing declarations, or schema
  failure are findings at the exact field; taste about unit choice is advisory.
- **Boundary:** A valid but unfamiliar unit or schema is not defective merely
  because the auditor would have chosen another one.

## CA-CONS-001 — Keep the artefact internally consistent

- **Severity:** BLOCKER
- **Applies to:** repeated claim IDs, task requirements, prose references,
  tables, code outputs, and metadata
- **Criterion:** Values or categorical assertions sharing a registered claim ID
  must agree after deterministic normalisation at the frozen printed-precision
  tolerance. A direct categorical mismatch is a finding. Any comparison needing
  conversion, aggregation, or arithmetic is sent to `referred_to_tools` and may
  block only if the frozen deterministic check confirms the disagreement.
- **Boundary:** Harmless formatting and differences within the frozen printed-
  precision tolerance are passed checks, not allegations.

## CA-METH-001 — Disclose material method limits and exclusions

- **Severity:** BLOCKER
- **Applies to:** method, assumption, limitation, input, output, and exclusion
  records
- **Criterion:** The recorded method ID and parameters match the method used by
  the shipped code/run manifest. Every declared input absent from the analysed
  output appears in the exclusion record with a reason. Every assumption or
  limitation marked material in the frozen task schema is present. Taste beyond
  these named records is advisory.
- **Boundary:** Preference for a different scientifically plausible method or
  parameter is advisory unless the frozen task explicitly requires it.

## CA-REPRO-001 — Preserve a credible rerun path

- **Severity:** BLOCKER
- **Applies to:** rerun and environment manifests
- **Criterion:** The artefact supplies a rerun command or job reference; every
  referenced path exists; code/input/environment identifiers resolve to shipped
  files or immutable external IDs; and the frozen dry-run validator can parse
  the command and manifest. Execution failure is blocking only when the task
  requires executable reproduction and the frozen tool confirms it.
- **Boundary:** Slow, inconvenient, or unfamiliar rerun machinery is not itself
  a blocker when every required identifier resolves.

## CA-META-001 — Treat missing required evidence explicitly

- **Severity:** BLOCKER
- **Applies to:** application of CA-TASK/EVD/DATA/CONS/METH/REPRO
- **Criterion:** If a field or artefact explicitly required by an applicable
  rule is absent or unreadable, create one finding citing that rule and the
  missing location. Do not infer compliance. Do not demand an artefact that no
  task requirement or applicable rule names.
- **Boundary:** The auditor cannot enlarge the evidence burden by inventing a
  new rule or silently importing another project's Constitution.

## CA-META-002 — Keep audit allegations grounded

- **Severity:** BLOCKER for audit integrity
- **Applies to:** audit reply
- **Criterion:** Every effective blocking finding contains an applicable C2
  rule ID, exact location, observed evidence, and affected requirement/claim ID
  where that schema supplies one. Unknown rule IDs, passed checks filed as
  findings, arithmetic-only allegations lacking deterministic confirmation, or
  missing required finding fields make the report an escalation rather than a
  pass.
- **Boundary:** Audit-integrity escalation preserves the allegation for review;
  it does not transform an unsupported allegation into a confirmed defect.
