# Seeded-Defect Pilot: Pre-Registration

**Question.** Does a cross-vendor (heterogeneous) LLM auditor catch defects in research
increments that a same-vendor (homogeneous) auditor misses — and vice versa?

**Registered before any audit runs.** The defect key is sealed: only its SHA-256
(`corpus/defect_key.sha256`) is committed before the arms run; the plaintext key is
revealed (committed) only after both arms' raw outputs are committed. Corpus, prompts,
rules, and scoring code are frozen at the commit that seals the key.

## Design

- **Corpus**: 30 synthetic experiment increments in the CrossAudit reference format
  (`metadata.yml`, `results.json`, `SUMMARY.md`), generated deterministically
  (`generate_corpus.py`, seed 20260730). 10 clean; 20 defective carrying ~45 seeded
  defects. Synthetic by design: zero disclosure of any real research, and fully
  reproducible by third parties. The corpus tests *auditor* capability, not generator
  provenance.
- **Arms** (identical prompt, identical Constitution = `examples/minimal/audit-repo/AUDIT_RULES.md`,
  temperature 0, same report schema; the ONLY variable is the model behind the endpoint):
  - `anthropic` — Claude-family auditor (same family as the notional generator ⇒ homogeneous arm)
  - `openai` — GPT-family auditor (⇒ heterogeneous arm)
- **Model pinning**: exact model IDs are set as repo variables `EXP_MODEL_ANTHROPIC` /
  `EXP_MODEL_OPENAI` and recorded verbatim in every output file.

## Defect taxonomy

DCL-visible (deterministic layer should catch; LLM audit runs *without* DCL here — we are
testing the model layer in isolation):
`D1` missing provenance (`source` absent) · `D2` unknown/wrong unit · `D3` convergence
violation (achieved > threshold, or converged=false) · `D4` missing required metadata field.

LLM-only (invisible to schema/unit/convergence scripts; requires reading):
`L1` metadata↔results contradiction (method or value mismatch) ·
`L2` silent exclusion (SUMMARY mentions dropped runs; `exclusions: []`) ·
`L3` cross-level comparison (SUMMARY compares quantities computed at different declared levels) ·
`L4` provenance mismatch (`source` cites a script not among declared inputs) ·
`L5` prose–number contradiction (SUMMARY states a sign/magnitude the JSON contradicts) ·
`L6` unconverged-as-established (SUMMARY quotes as final a quantity whose convergence
block fails or is absent).

## Metrics

Per arm: recall by defect class (lenient match: finding in the right increment citing the
right rule family; strict match: + location substring); false-positive count on the 10
clean increments; verdict accuracy (BLOCKED iff increment carries a BLOCKER-class defect).
Ambiguous matches go to `scoring/adjudication.jsonl`, committed with reasons.

## Honesty constraints

- No prompt tells the auditor that defects were seeded, how many, or of what kind.
- Both arms run from the same frozen commit; reruns are new files, never overwrites.
- Negative or null results are reported in the paper regardless of direction.
- This is a pilot (n≈45 defects): it bounds effect sizes and demonstrates the harness;
  it does not power fine class-level comparisons.

## Workflow

`.github/workflows/experiment.yml` runs each arm in GitHub Actions (matrix), using repo
secrets `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, and commits raw outputs to
`experiment/results/<arm>/`. Trigger: `workflow_dispatch`, or a push touching
`experiment/RUN_TRIGGER`. Scoring (`score.py`) runs locally/CI after both arms land and
writes `experiment/results/SCORECARD.md`.
