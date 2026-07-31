# CA-CODE rule family (draft template, revision 0)

Decidable-first rules for auditing generator-written code. Severities follow
the two-level scheme; every rule keeps the standard fields (ID, severity,
acceptance criterion, checked-by). New deployments should adopt these as
ADVISORY and promote via the shadow-mode ratchet once their ledger supports it.

| ID | Severity | Acceptance criterion (decidable core) | Checked by |
|---|---|---|---|
| CA-CODE-001 | BLOCKER | every script carries a contract header: inputs, outputs, units, side effects | DCL (header parser) |
| CA-CODE-002 | BLOCKER | every numeric transformation is covered by a test containing one hand-computed worked example | DCL (diff-coverage + test naming convention) |
| CA-CODE-003 | BLOCKER | no bare `except`, no silent NaN/None propagation on numeric paths | DCL (lint rules) |
| CA-CODE-004 | BLOCKER | dependencies pinned; interpreter version declared | DCL (manifest check) |
| CA-CODE-005 | BLOCKER | all stochastic steps take an explicit seed recorded in the increment metadata | DCL (lint + metadata cross-check) |
| CA-CODE-006 | BLOCKER | script output validates against the data increment schema it claims to produce | DCL (dry-run on fixture + schema check) |
| CA-CODE-101 | ADVISORY | the implementation matches the increment's stated method (semantic review; cite the mismatching lines as evidence) | Auditor (LLM) |
| CA-CODE-102 | ADVISORY | unit handling is explicit end-to-end (no implicit eV/kcal/mol, Å/bohr conversions) | Auditor, partially lintable |
| CA-CODE-103 | ADVISORY | numerical-stability hazards (catastrophic cancellation, unguarded division, tolerance choices) are absent or justified | Auditor (LLM) |

Design note. CA-CODE-101..103 are deliberately ADVISORY: they are the
review-only stratum where letter-vs-intent divergence between vendors is
expected and informative. Findings there must cite file and line as evidence
(I3 applies unchanged). A deployment that finds 101-class findings recurring
undisputed should tighten its 00x-series decidable rules instead of promoting
the judgment call — encode the lesson, not the opinion.
