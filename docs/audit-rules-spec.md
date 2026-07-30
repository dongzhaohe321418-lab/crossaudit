# Writing the Constitution: rule specification

The Constitution (`AUDIT_RULES.md`) is the single highest-leverage file in a CrossAudit deployment. The Auditor cannot exceed it; the Generator will learn its gaps. This guide specifies the format and the craft.

## Rule format

Every rule is a block with five fields:

```markdown
### CA-DATA-001 — Every reported quantity carries units and provenance
- **Severity:** BLOCKER
- **Applies to:** experiments/**/results.json
- **Criterion:** Each numeric entry in `results` has non-empty `unit` and `source`
  (a script name + commit, or an instrument/dataset identifier). Decidable by
  inspection of the file alone.
- **Rationale:** A number without units and origin cannot be checked by anyone,
  human or machine, now or later.
```

Field semantics:

- **ID** — `CA-<SECTION>-<NNN>`. Stable forever; never reuse a retired ID. Sections in the template: `DATA` (data integrity), `METH` (methodology floor), `REPRO` (reproducibility), `DOM` (domain-specific), `META` (rules about the audit itself).
- **Severity** — `BLOCKER` or `ADVISORY` only. See `architecture.md` §4 for why there is no third level.
- **Applies to** — a path glob. Rules the Auditor cannot map to files invite hallucinated findings.
- **Criterion** — the heart. Must be *decidable*: a competent reader (human or LLM) inspecting the named artifacts can answer pass/fail without further judgement. If you cannot phrase it decidably, its severity must be `ADVISORY`, or it belongs in the DCL as a script instead.
- **Rationale** — one or two sentences. The Auditor quotes this in reports; the Generator reads it when disputing. Rules without rationales get litigated.

## The craft: seven principles

1. **Decidable or advisory — no middle.** "Methodology should be appropriate" is not enforceable and trains the Auditor to bluff. Either sharpen it ("SCF convergence threshold ≤ 1e-6 Ha unless metadata declares why not") or mark it `ADVISORY`.
2. **If a script can check it, a script should.** Constitution rules that duplicate mechanisable checks belong in `checks/`. The Constitution covers what needs *reading*: consistency between prose claims and data, provenance plausibility, declared-vs-actual methods.
3. **Write for the disputing Generator, not just the Auditor.** Every `BLOCKER` will eventually be disputed. A rule whose criterion cites concrete artifacts survives disputes; vibes do not.
4. **Domain sections are yours; keep the core generic.** `CA-DATA/METH/REPRO/META` should transfer across fields unchanged; put field lore in `CA-DOM-*`.
5. **Version like law.** Changes are commits with messages explaining *why the rule changed*. Reports cite the Constitution hash (invariant I3), so history answers "which rules governed experiment X".
6. **Include META rules** — rules about auditing itself: what the Auditor must do when evidence is missing (`CA-META-001`: missing evidence is a finding, not a pass), when it may not decide (`CA-META-003`: matters of scientific taste → note as ADVISORY, never BLOCKER), what makes its own report invalid.
7. **Grow it from escalations.** Every human escalation that ends in "the rulebook was silent" should end, additionally, in a rule PR. The Constitution is a living record of what supervision has had to learn.

## Anti-patterns

- **The omniscience rule** — "The Auditor shall verify the results are correct." It cannot; nobody can from text alone. Decompose into checkable provenance/consistency rules.
- **Severity inflation** — everything `BLOCKER`. The pipeline halts daily, the human starts rubber-stamping escalations, and the system dies of alert fatigue. Default new rules to `ADVISORY`; promote with evidence.
- **The silent waiver** — letting the Generator's dispute *edit the rule inline*. Rule changes go through the human's PR review, never through the loop.
- **Unbounded scope** — `Applies to: **/*`. Auditors given everything check nothing.
