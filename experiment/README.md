# experiment/ — generation map

Three generations of the seeded-defect programme share this directory. v1 sits
at the top level because the paper and the registration documents cite those
paths; moving it into a `v1/` folder would rewrite paths that frozen documents
refer to, so the layout stays and this file does the mapping instead (sixth
audit, R9).

| Generation | Where | Status | Registration / authority |
|---|---|---|---|
| **v1** — three-arm seeded-defect pilot | top level: `DESIGN.md`, `generate_corpus.py`, `corpus/`, `defect_key.json`, `run_arm.py`, `score.py`, `score_nullcheck.py`, `scoring/`, `results/` | **Finished, frozen.** Results in `results/SCORECARD.md` (dual-map) and `results/NULLCHECK.json` (permutation floors). Runner archived: `.github/workflows-archive/experiment.yml`. | `DESIGN.md` + its pre-execution Amendment 1 |
| **v2** — scoring revision | `v2/`, registered in `v2-REGISTRATION.md` | Scorer committed; superseded as the reportable scorer by the dual-map report in v1's `score.py`. | `v2-REGISTRATION.md` |
| **v3** — isolation-ladder ablation (Parts A/B/C) | `v3/`: `RUNBOOK.md`, `mine_ledger.py`, `real-ledger/` (Part B, mined & frozen), `partC/` (code-audit pilot harness) | **Registered and frozen; key-gated.** Part B data mined; Part C pilot ran key-less (kill matrix committed). Model arms await operator keys + defect-key escrow. | `v3-ABLATION-REGISTRATION.md` + Amendments 1–2 — **beats everything else on conflict**, including `improvements/` |

Precedence within this directory follows `CLAUDE.md`: registration documents
(with their dated amendments) are the source of truth; READMEs and design notes
explain but never override. The scoring maps in `score.py` and the label rules
in the v3 registration never change after outputs exist — amend via dated
AMENDMENT sections only (`v3/RUNBOOK.md` §8).
