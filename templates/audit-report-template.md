# Audit Report — [science-repo]@[short-sha]

| | |
|---|---|
| **Increment** | `[owner/science-repo]` commit `[full sha]` |
| **Paths audited** | `experiments/[...]` |
| **Round** | [k] of [max_rounds] |
| **Constitution** | `AUDIT_RULES.md` @ `[constitution commit hash]` |
| **Deterministic checks** | [PASS / FAIL — n hard failures] (`checks.json` attached) |
| **Verdict** | **[PASS / BLOCKED / ESCALATE]** |
| **Auditor** | [model identifier, vendor B] |

## Findings

> One block per finding. No findings under a section ⇒ state "No findings."
> A BLOCKER without a rule citation is invalid (CA-META-002/003).

### [BLOCKER] CA-DATA-002 — metadata/results mismatch
- **Artifact:** `experiments/2026-.../results.json` vs `metadata.yml`
- **Observation:** [what was found, quoting the exact values/lines]
- **Criterion violated:** [quote the rule's criterion clause]
- **Required to clear:** [the minimal change that would satisfy the criterion]

### [ADVISORY] CA-METH-003 — [title]
- **Artifact:** [...]
- **Observation:** [...]
- **Suggestion:** [...]

## Section checklist

| Section | Rules applied | Findings |
|---|---|---|
| DATA | CA-DATA-001..003 | [0 BLOCKER / 0 ADVISORY] |
| METH | CA-METH-001..003 | [...] |
| REPRO | CA-REPRO-001..002 | [...] |
| DOM | CA-DOM-001..002 | [...] |
| META | CA-META-001..004 | [...] |

## Deterministic check output

```json
[inline checks.json]
```

## Notes for the human (asynchronous)

[Optional: patterns across recent increments, Constitution gaps observed, suggested rule PRs.]
