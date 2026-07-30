# Hardened rerun — registration (v2, NOT YET RUN)

Registered design meeting the minimum conditions set by the 2026-07-30 cross-vendor
audit (`audits/`). Nothing below has executed; this file freezes the plan.

1. **Key custody.** The defect key and generator seed are held by an independent party
   (or an encrypted commit whose passphrase is escrowed off-repo); only the SHA-256
   commitment is public before reveal. The generator is NOT committed publicly before
   the run (the v1 flaw: a public deterministic generator makes the key derivable).
2. **Freeze before run.** Corpus, prompts, Constitution, scorer, model IDs, and the
   execution workflow are pinned by commit hash in this file's next revision, before
   any arm runs. Later scoring changes are labelled exploratory, never headline.
3. **One runner, both arms.** Both model arms run through `run_arm.py` in CI with
   temperature 0 and full provenance (prompt/system/response SHA-256, model ID,
   timestamps, runner commit). No subagent execution.
4. **Per-defect binding.** Corpus v2 assigns each defect a unique ID and location;
   scoring requires a single finding to match rule-family AND location for that ID
   (no cross-defect credit from one finding; no increment-level token soup).
   Adjudication is done by an arm-blinded third model, logged.
5. **Controls.** Corpus v2 adds: L3-only increments (severity-discipline test),
   out-of-scope-defect increments (should NOT be blocked), subtle LLM-authored
   defects (anti-ceiling), and ≥3 seeds. Clean-increment count sized so a zero-FP
   observation bounds the FP rate below 10% (n ≥ 29 clean) at one-sided 95%.
6. **Reporting.** Recall with binomial CIs per class; BLOCKER FPs and ADVISORY burden
   reported separately; verdict accuracy split by increment type; all raw outputs
   committed before reveal.

Trigger condition: operator supplies fresh API keys (previous keys were exposed in a
chat channel and must be considered burned) and approves the run cost (~2× v1).
