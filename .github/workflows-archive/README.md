# Archived workflows

GitHub only runs workflows under `.github/workflows/`, so anything here is
inert by construction. Files are kept rather than deleted because they are part
of the ledger: `experiment.yml` is the runner that produced
`experiment/results/` and is cited by the paper's account of the seeded-defect
trial.

## experiment.yml — disarmed 2026-07-31 (sixth audit, R6/R11)

It triggered on any push to `main` touching `experiment/RUN_TRIGGER`, ran both
vendor arms with `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`, and auto-committed
raw outputs with `contents: write`. The v1 trial is finished and its results are
frozen, so a stray touch of that file could only spend keys and append to a
frozen result set. `experiment/RUN_TRIGGER` was deleted in the same commit.

Its default model pins (`claude-sonnet-4-5`, `gpt-5.1`) are stale with respect
to the v3 registration. If a rerun is ever wanted, do not simply move this file
back: re-pin the models to what the registration names, and re-read
`experiment/v3/RUNBOOK.md` §8 first — the red lines about sealed keys and
no-peek arm ordering apply to any rerun, not only to the first one.
