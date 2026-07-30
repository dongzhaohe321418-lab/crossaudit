# Contributing to CrossAudit

Thank you for considering a contribution. CrossAudit is a protocol first and a codebase second, so contributions are welcome at both levels.

## What is most useful right now

1. **Field adapters** — deterministic check sets and Constitution domain sections for fields beyond computational chemistry (bioinformatics, materials, ML research, econometrics…). Add them under `examples/<field>/` with a short README.
2. **Auditor adapters** — `run_llm_audit.py` currently ships an OpenAI-compatible client and an offline stub. Adapters for other vendors (kept behind the same report schema) are welcome.
3. **War stories** — if you run the loop in a real pipeline, an issue describing what the auditor caught (or missed) is a first-class contribution. The threat model in `docs/architecture.md` grows from these.
4. **Constitution rules** — well-formed, decidable rules for the template, with severity and acceptance criteria.

## Ground rules

- Keep the core dependency-light: the check layer stays stdlib + PyYAML; the glue stays plain GitHub Actions. Platform lock-in defeats the purpose.
- Every rule proposed for `templates/AUDIT_RULES.md` must state a decidable acceptance criterion. "The method should be sound" is not a rule; "every reported energy must carry a basis-set label" is.
- Do not weaken the two invariants: auditor vendor ≠ generator vendor, and deterministic check verdicts are non-overridable by any LLM.
- English for code and docs; bilingual (EN/zh-CN) READMEs are maintained together — if you change one, flag the other in your PR.

## Process

Fork → branch → PR against `main`, with a description of what the change does and why. For protocol-level changes (severity semantics, escalation policy, report schema), open an issue for discussion first.

## Licence

By contributing you agree that your contributions are licensed under the MIT licence of this repository.
