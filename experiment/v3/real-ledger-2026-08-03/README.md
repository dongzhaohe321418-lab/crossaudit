# Second ledger snapshot — 3 August 2026 (operational telemetry only)

Mined with `../mine_ledger.py` from the live deployment at science
`735e7f00`, audit `abb10a47`. The first snapshot (`../real-ledger/`, science
`af0dc587`, audit `88b92429`, 31 July) remains the **frozen Part B dataset**
of `experiment/v3-ABLATION-REGISTRATION.md`. Nothing here is admissible as
Part B evidence; these records exist so the paper's section 4.2 telemetry can
be checked and so the eventual v3 run can quote growth honestly.

At this snapshot: 21 model-audited cycles, 23 distinct findings, 20
behaviourally confirmed, 3 unresolved. Severity mix (deployment's own
four-level ladder): 3 CRITICAL, 13 HIGH, 4 MEDIUM, 3 LOW. Median closure lag
1 cycle (range 1-8). Twelve findings cite one provenance gate. Auditor model
identifiers vary across the run (gpt-5 x12, gpt-5.6 x5, gpt-5.6-sol x2,
"GPT-5" x1), so the series mixes configurations and cannot support arm
comparison — recorded here, not narrated away.
