# Real deployment ledger — mined summary (Level-B redacted)

Freeze: science `af0dc587`, audit `88b92429` (2026-07-31). Source of truth:
`cycles.jsonl`, `findings_lifecycle.json`, `summary.json` beside this file;
regenerate with `../mine_ledger.py`.

| Cycle | Audited commit | Decision | Findings | Closed-confirmed here | Model |
|---|---|---|---|---|---|
| CYCLE-000001 | 81fd505e | BLOCK | 7 | 0 | (unrecorded) |
| CYCLE-000002 | bfece650 | BLOCK | 4 | 5 | gpt-5.6 |
| CYCLE-000004 | 746564b6 | BLOCK | 3 | 0 | gpt-5.6 |
| CYCLE-000005 | b7de4784 | BLOCK | 2 | 3 | gpt-5 |
| CYCLE-000006 | 4aed10a9 | BLOCK | 1 | 2 | gpt-5 |
| CYCLE-000007 | 4ccb0cd6 | PASS_WITH_CAVEATS | 1 | 1 | gpt-5.6-sol |
| CYCLE-000008 | af0dc587 | PASS | 0 | 1 | gpt-5 |

Headline: 14 distinct findings; 12 behaviourally confirmed real (fixes named
and verified closed), 2 unresolved at freeze; finding count decays
7-4-3-2-1-1-0 across two days to a PASS; every revise leg is a science-repo
commit naming the finding IDs it closes. CYCLE-000003 exists only as a
science-side "Tier-0 follow-up" leg (no model-audit artifact), reported
as-is.

The severity/scope/rule-citation structure per finding is in
`findings_lifecycle.json` (titles committed as sha256 prefixes; full text
lives only in the source repositories).
