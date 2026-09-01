# C0 — No substantive Constitution

**Registered level:** C0
**Purpose:** estimate the auditor's model prior under the same reply contract,
without supplying substantive quality rules.

The auditor receives the task specification and artefact bundle. It reports
only defects it can substantiate from those materials. C0 supplies no
project-quality rule IDs, severities, acceptance criteria, or permission to
invent them.

The common reply contract remains in force because it is measurement plumbing,
not a substantive Constitution:

- passed checks go in `checks_performed`, never `findings`;
- matters requiring deterministic arithmetic go in `referred_to_tools`;
- a finding states one concrete allegation and one location;
- empty findings means no defect alleged;
- the reply must conform to the frozen JSON schema; and
- the auditor must not infer generator identity, defect count, or study arm.

Findings under C0 do not cite `CA-*` rules. Any remembered or invented rule ID is
counted as an ungrounded citation and retained in burden/false-block analyses.
