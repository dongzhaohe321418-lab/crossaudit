# Seeded-Defect Pilot — Scorecard (dual-map report)

Key hash verified against corpus/defect_key.sha256: `5132b1c25b99bf52…`
NOTE (audit 2026-07-30): the key file was inadvertently public from the
registration commit onward and is derivable from the public seeded generator;
'sealed' is therefore NOT claimed. FROZEN = scoring map as committed before
outputs; ADJUDICATED = post-hoc map per scoring/adjudication.jsonl (exploratory).

# --- FROZEN scoring map ---
## Arm `anthropic-subagent` — model `claude-fable-5 (fresh-context subagent, session sampling)`

- Lenient recall: **38/43**; strict: **38/43**
- False-positive BLOCKERs on clean increments: **0**
- Verdict accuracy: **30/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 0 | 0 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 2 | 2 | 2 |
| L1 | 5 | 5 | 5 |
| L2 | 5 | 5 | 5 |
| L3 | 2 | 2 | 3 |
| L4 | 6 | 6 | 6 |
| L5 | 7 | 7 | 7 |
| L6 | 5 | 5 | 5 |

## Arm `dcl` — model `checks@dbe5a94`

- Lenient recall: **17/43**; strict: **17/43**
- False-positive BLOCKERs on clean increments: **0**
- Verdict accuracy: **25/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 4 | 4 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 2 | 2 | 2 |
| L1 | 0 | 0 | 5 |
| L2 | 0 | 0 | 5 |
| L3 | 0 | 0 | 3 |
| L4 | 0 | 0 | 6 |
| L5 | 0 | 0 | 7 |
| L6 | 5 | 5 | 5 |

## Arm `openai` — model `gpt-5.1`

- Lenient recall: **41/43**; strict: **37/43**
- False-positive BLOCKERs on clean increments: **26**
- Verdict accuracy: **20/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 4 | 4 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 1 | 1 | 2 |
| L1 | 5 | 5 | 5 |
| L2 | 5 | 5 | 5 |
| L3 | 3 | 1 | 3 |
| L4 | 5 | 3 | 6 |
| L5 | 7 | 7 | 7 |
| L6 | 5 | 5 | 5 |

# --- ADJUDICATED scoring map ---
## Arm `anthropic-subagent` — model `claude-fable-5 (fresh-context subagent, session sampling)`

- Lenient recall: **43/43**; strict: **43/43**
- False-positive BLOCKERs on clean increments: **0**
- Verdict accuracy: **30/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 4 | 4 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 2 | 2 | 2 |
| L1 | 5 | 5 | 5 |
| L2 | 5 | 5 | 5 |
| L3 | 3 | 3 | 3 |
| L4 | 6 | 6 | 6 |
| L5 | 7 | 7 | 7 |
| L6 | 5 | 5 | 5 |

## Arm `dcl` — model `checks@dbe5a94`

- Lenient recall: **19/43**; strict: **17/43**
- False-positive BLOCKERs on clean increments: **0**
- Verdict accuracy: **25/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 4 | 4 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 2 | 2 | 2 |
| L1 | 0 | 0 | 5 |
| L2 | 0 | 0 | 5 |
| L3 | 2 | 0 | 3 |
| L4 | 0 | 0 | 6 |
| L5 | 0 | 0 | 7 |
| L6 | 5 | 5 | 5 |

## Arm `openai` — model `gpt-5.1`

- Lenient recall: **41/43**; strict: **37/43**
- False-positive BLOCKERs on clean increments: **26**
- Verdict accuracy: **20/30**

| class | lenient | strict | n |
|---|---|---|---|
| D1 | 5 | 5 | 5 |
| D2 | 4 | 4 | 4 |
| D3 | 1 | 1 | 1 |
| D4 | 1 | 1 | 2 |
| L1 | 5 | 5 | 5 |
| L2 | 5 | 5 | 5 |
| L3 | 3 | 1 | 3 |
| L4 | 5 | 3 | 6 |
| L5 | 7 | 7 | 7 |
| L6 | 5 | 5 | 5 |
